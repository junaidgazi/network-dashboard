"""
Home Network Monitoring Dashboard
-----------------------------------
Scans your local network for connected devices, tracks whether each
one is online/offline over time, and serves a live dashboard.

HOW IT WORKS (read this before you touch the code):
1. We figure out your computer's own IP address and subnet (e.g. 192.168.1.x)
2. We "ping" every possible address in that range (1-254) at the same time
   using multiple threads, so it's fast instead of taking minutes
3. Whichever addresses respond = devices that are online right now
4. We save that result to a small database (SQLite - just a file, no setup)
5. We repeat this every 30 seconds in the background
6. The webpage asks our API "what's the status right now?" every few
   seconds and updates itself - this is called "polling"
"""

import socket
import sqlite3
import subprocess
import platform
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, jsonify, render_template

app = Flask(__name__)

DB_PATH = "network.db"
SCAN_INTERVAL_SECONDS = 30   # how often we re-scan the network
PING_TIMEOUT_SECONDS = 1     # how long to wait for each device to respond
MAX_WORKERS = 50             # how many devices we ping at the same time


# ---------- Database setup ----------
# SQLite stores everything in one file (network.db) that gets created
# automatically the first time this runs. Two tables:
#   devices - the latest known status of each IP address
#   history - a log of every scan result, used to draw the uptime chart

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            ip TEXT PRIMARY KEY,
            hostname TEXT,
            status TEXT,
            last_seen TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            status TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


# ---------- Network scanning ----------

def get_local_subnet():
    """Find our own IP address, then assume the network is a /24
    (meaning: same first three numbers, last number 1-254).
    e.g. if our IP is 192.168.1.42, we scan 192.168.1.1 - 192.168.1.254
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This doesn't actually send data anywhere, it's a trick to ask
        # the OS "what IP would I use to reach the internet?"
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    subnet_prefix = ".".join(local_ip.split(".")[:3])
    return subnet_prefix, local_ip


def ping(ip):
    """Ping one address. Returns True if it responded, False if not.
    Windows and Mac/Linux use slightly different ping command flags,
    so we detect the OS first.
    """
    is_windows = platform.system().lower() == "windows"
    count_flag = "-n" if is_windows else "-c"
    timeout_flag = "-w" if is_windows else "-W"
    timeout_value = str(PING_TIMEOUT_SECONDS * 1000) if is_windows else str(PING_TIMEOUT_SECONDS)

    command = ["ping", count_flag, "1", timeout_flag, timeout_value, ip]
    try:
        result = subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=PING_TIMEOUT_SECONDS + 1
        )
        return result.returncode == 0
    except Exception:
        return False


def get_hostname(ip):
    """Try to look up a friendly device name. Often fails for phones/IoT
    devices, that's normal - we just fall back to showing the IP.
    """
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


def scan_network():
    """The main scan: ping every address in our subnet at once using a
    thread pool (ThreadPoolExecutor = 'run up to MAX_WORKERS of these
    at the same time instead of one after another').
    """
    subnet_prefix, local_ip = get_local_subnet()
    addresses = [f"{subnet_prefix}.{i}" for i in range(1, 255)]

    online_ips = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_ip = {executor.submit(ping, ip): ip for ip in addresses}
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            if future.result():
                online_ips.append(ip)

    save_scan_results(subnet_prefix, addresses, online_ips)
    return online_ips


def save_scan_results(subnet_prefix, all_addresses, online_ips):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat()
    online_set = set(online_ips)

    for ip in all_addresses:
        status = "online" if ip in online_set else "offline"

        # Only bother with hostname + history writes for addresses we've
        # actually seen respond at some point, to keep the DB small.
        cur = conn.execute("SELECT ip FROM devices WHERE ip = ?", (ip,))
        exists = cur.fetchone() is not None

        if status == "online" or exists:
            hostname = get_hostname(ip) if status == "online" else None
            conn.execute(
                """INSERT INTO devices (ip, hostname, status, last_seen)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(ip) DO UPDATE SET
                     status=excluded.status,
                     last_seen=CASE WHEN excluded.status='online' THEN excluded.last_seen ELSE devices.last_seen END,
                     hostname=COALESCE(excluded.hostname, devices.hostname)
                """,
                (ip, hostname, status, now),
            )
            conn.execute(
                "INSERT INTO history (ip, status, timestamp) VALUES (?, ?, ?)",
                (ip, status, now),
            )

    conn.commit()
    conn.close()


def background_scanner():
    """Runs forever in a separate thread, scanning on a timer."""
    while True:
        try:
            scan_network()
        except Exception as e:
            print(f"Scan error: {e}")
        time.sleep(SCAN_INTERVAL_SECONDS)


# ---------- API routes ----------
# These are the URLs the webpage's JavaScript will "fetch" data from.

@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/api/devices")
def api_devices():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT ip, hostname, status, last_seen FROM devices ORDER BY status DESC, ip"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/history/<ip>")
def api_history(ip):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT status, timestamp FROM history WHERE ip = ? ORDER BY timestamp DESC LIMIT 50",
        (ip,),
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in reversed(rows)])


@app.route("/api/summary")
def api_summary():
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
    online = conn.execute("SELECT COUNT(*) FROM devices WHERE status='online'").fetchone()[0]
    conn.close()
    _, local_ip = get_local_subnet()
    return jsonify({"total_known_devices": total, "online_now": online, "your_ip": local_ip})


if __name__ == "__main__":
    init_db()
    # Run one scan immediately on startup so the dashboard isn't empty,
    # then let the background thread take over repeating scans.
    threading.Thread(target=scan_network, daemon=True).start()
    threading.Thread(target=background_scanner, daemon=True).start()
    app.run(debug=True, port=5000)
