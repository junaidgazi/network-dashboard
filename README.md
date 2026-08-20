# Home Network Monitoring Dashboard

A full-stack network monitoring tool built with Python and Flask that scans and tracks device connectivity across a local network in real time, using multithreading to scan 250+ addresses in under 3 seconds.

## How to run it

1. Clone this repo
2. Install dependencies: `pip3 install -r requirements.txt`
3. Run: `python3 app.py`
4. Open `http://127.0.0.1:5000` in your browser

## What it does

- Scans your local network and identifies all connected devices
- Shows online/offline status live, updating every 5 seconds
- Tracks device history using SQLite
- Built using a thread pool to scan the network in parallel instead of one device at a time

## Skills demonstrated

Python, REST API design (Flask), networking fundamentals (IP addressing, subnets, ICMP), concurrent programming, SQL/databases, frontend basics (HTML/JS, live polling)
