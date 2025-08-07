# Tail OpenCanary log and send ntfy alerts
import os, time, json, requests, argparse
from dotenv import load_dotenv
load_dotenv()

LOG = os.getenv("OPENCANARY_LOG", "/logs/opencanary/opencanary.log")

server = os.getenv("NTFY_SERVER", "http://localhost").rstrip("/")
topic  = os.getenv("NTFY_TOPIC", "ghostmode-alerts")
user   = os.getenv("NTFY_USER") or None
pw     = os.getenv("NTFY_PASS") or None

def alert(msg):
    url = f"{server}/{topic}"
    auth = (user, pw) if user and pw else None
    try:
        requests.post(url, data=msg.encode("utf-8"), auth=auth, timeout=5)
    except Exception as e:
        print("[ntfy error]", e)

def format_evt(evt: dict) -> str:
    ts = evt.get("local_time") or evt.get("timestamp") or "unknown"
    node = evt.get("node_id", "node")
    svc  = evt.get("service", "?")
    src  = evt.get("src_host", "?")
    port = evt.get("dst_port", "?")
    return f"[OpenCanary] {ts} node={node} service={svc} src={src} port={port}"

def parse(line):
    try:
        evt = json.loads(line.strip())
        return format_evt(evt)
    except Exception:
        return None

def tail(path):
    with open(path, "r") as f:
        f.seek(0, os.SEEK_END)
        inode = os.fstat(f.fileno()).st_ino
        while True:
            line = f.readline()
            if line:
                yield line
            else:
                time.sleep(0.5)
                try:
                    if os.stat(path).st_ino != inode:
                        with open(path, "r") as nf:
                            f.close()
                            f = nf
                            inode = os.fstat(f.fileno()).st_ino
                            f.seek(0, os.SEEK_END)
                except FileNotFoundError:
                    time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default=LOG)
    args = parser.parse_args()

    print(f"Tailing {args.log} ...")
    for line in tail(args.log):
        msg = parse(line)
        if msg:
            print(msg)
            alert(msg)
