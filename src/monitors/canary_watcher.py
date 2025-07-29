#!/usr/bin/env python3
"""
canary_watcher.py
Tail & parse OpenCanary JSON log and send real-time alerts via Signal or ntfy.

Usage examples:
  # Signal
  python canary_watcher.py --log /var/log/opencanary.log \
      --signal-phone +19999999999 --signal-recipient +18888888888

  # ntfy
  python canary_watcher.py --log /var/log/opencanary.log \
      --ntfy-url https://ntfy.yourserver.tld/topic

(You can also set these via environment variables; see argparse defaults.)
"""

import os
import time
import json
import argparse
import subprocess
from typing import Optional

try:
    import requests  # for ntfy
except ImportError:
    requests = None


def alert_signal(message: str, phone: str, recipient: str):
    if not phone or not recipient:
        print("[warn] Signal alert requested but phone/recipient not provided.")
        return
    try:
        subprocess.run(
            ["signal-cli", "-u", phone, "send", recipient, "-m", message],
            check=False,
        )
    except Exception as e:
        print(f"[error] signal-cli failed: {e}")


def alert_ntfy(message: str, url: str):
    if not url:
        print("[warn] ntfy alert requested but URL not provided.")
        return
    if requests is None:
        print("[warn] requests is not installed; ntfy alert skipped.")
        return
    try:
        requests.post(url, data=message.encode("utf-8"), timeout=5)
    except Exception as e:
        print(f"[error] ntfy failed: {e}")


def format_event(evt: dict) -> str:
    ts = evt.get("local_time") or evt.get("timestamp") or "unknown-time"
    node = evt.get("node_id", "unknown-node")
    service = evt.get("service", "unknown-service")
    port = evt.get("dst_port", "?")
    src = evt.get("src_host", "unknown-src")
    d = evt.get("logdata", {})
    # Extra detail if available
    extra = []
    if isinstance(d, dict):
        for k in ("USERNAME", "PASSWORD", "SENSORID", "PUBLICKEY", "URL", "DATA"):
            if k in d:
                extra.append(f"{k}={d[k]}")
    extra_txt = (" " + " ".join(extra)) if extra else ""
    return f"[OpenCanary] time={ts} node={node} service={service} port={port} src={src}{extra_txt}"


def parse_json_line(line: str) -> Optional[str]:
    try:
        evt = json.loads(line.strip())
        return format_event(evt)
    except Exception:
        return None


def tail_file(path: str):
    """
    Minimalistic tail -F style reader (no external deps).
    Will re-open file on truncate/rotation.
    """
    with open(path, "r") as f:
        # seek to end
        f.seek(0, os.SEEK_END)
        inode = os.fstat(f.fileno()).st_ino

        while True:
            where = f.tell()
            line = f.readline()
            if line:
                yield line
            else:
                time.sleep(0.5)
                # Handle rotation
                try:
                    if os.stat(path).st_ino != inode:
                        # File rotated
                        with open(path, "r") as nf:
                            f.close()
                            f = nf
                            inode = os.fstat(f.fileno()).st_ino
                            f.seek(0, os.SEEK_END)
                except FileNotFoundError:
                    # File temporarily missing, wait and retry
                    time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="Tail OpenCanary log & alert.")
    parser.add_argument("--log", default=os.getenv("OPENCANARY_LOG", "/var/log/opencanary.log"))
    # Signal
    parser.add_argument("--signal-phone", default=os.getenv("SIGNAL_PHONE"))
    parser.add_argument("--signal-recipient", default=os.getenv("SIGNAL_RECIPIENT"))
    # ntfy
    parser.add_argument("--ntfy-url", default=os.getenv("NTFY_URL"))
    # Mode
    parser.add_argument("--alert", choices=["signal", "ntfy", "both", "print"], default=os.getenv("ALERT_MODE", "print"))
    args = parser.parse_args()

    print(f"[*] Tailing {args.log} ... alert mode: {args.alert}")

    for line in tail_file(args.log):
        msg = parse_json_line(line)
        if not msg:
            continue
        print(msg)

        if args.alert in ("signal", "both"):
            alert_signal(msg, args.signal_phone, args.signal_recipient)
        if args.alert in ("ntfy", "both"):
            alert_ntfy(msg, args.ntfy_url)


if __name__ == "__main__":
    main()
