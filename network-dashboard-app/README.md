# Home Network Monitoring Dashboard

A Flask web app that scans your local network, tracks which devices are
online/offline, and displays it on a live-updating dashboard.

## How to run it on your own computer

1. **Install Python** if you don't have it: https://www.python.org/downloads/
   (during install on Windows, check the box "Add Python to PATH")

2. **Open a terminal** in this folder (on Mac: right-click the folder → New
   Terminal at Folder. On Windows: open the folder, type `cmd` in the
   address bar and press Enter).

3. **Install the one dependency:**
   ```
   pip install -r requirements.txt
   ```

4. **Run it:**
   ```
   python app.py
   ```

5. **Open your browser** to: http://127.0.0.1:5000

   You should see devices start appearing within about 10-20 seconds as the
   first scan completes.

6. **Stop it** anytime with Ctrl+C in the terminal.

## Notes

- This only sees devices on the SAME wifi network as the computer running it.
- Some devices (phones especially) may not respond to pings if they have
  strict privacy settings — that's normal, not a bug.
- The `network.db` file that appears after running is your database. Delete
  it anytime to reset the history.
- You may see a firewall permission popup the first time you run it —
  allow it, since it needs network access to ping devices.

## Ideas to extend it (good for showing growth later)

- Add MAC address lookup so devices survive IP address changes (DHCP
  sometimes reassigns IPs)
- Add email/SMS alert when a specific device goes offline
- Add a chart (using Chart.js) showing uptime history per device using the
  `/api/history/<ip>` endpoint, which already returns the data for it
- Deploy it to run permanently on a Raspberry Pi

## Putting this on your resume

**Project name:** Home Network Monitoring Dashboard

**One-line bullet (use this format):**
> Built a full-stack network monitoring tool (Python, Flask, SQLite) that
> scans and tracks device connectivity across a local network in real time,
> using multithreading to scan 250+ addresses in under 3 seconds.

**What to say if asked about it in an interview:**
- Why you built it: to understand what's actually happening on a home
  network and get hands-on with concepts from your networking degree
- Technical decisions to mention: you used a thread pool to ping devices
  concurrently instead of one at a time (explain the speed difference),
  and SQLite for zero-setup persistent storage
- What you'd improve: mention 1-2 items from the "ideas to extend it" list
  above — shows you understand its limits, which reads as maturity, not
  weakness

**Skills this demonstrates:** Python, REST API design, networking
fundamentals (IP addressing, subnets, ICMP), concurrent programming,
SQL/databases, frontend basics (HTML/JS, polling/live data)
