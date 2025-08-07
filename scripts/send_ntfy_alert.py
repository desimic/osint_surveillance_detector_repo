import os, requests
from dotenv import load_dotenv

load_dotenv()
server = os.getenv("NTFY_SERVER", "http://localhost").rstrip("/")
topic = os.getenv("NTFY_TOPIC", "ghostmode-alerts")
user = os.getenv("NTFY_USER") or None
pw = os.getenv("NTFY_PASS") or None

def send(msg):
    url = f"{server}/{topic}"
    auth = (user, pw) if user and pw else None
    r = requests.post(url, data=msg.encode("utf-8"), auth=auth, timeout=10)
    print("ntfy:", r.status_code, r.text[:120])

if __name__ == "__main__":
    send("✅ Ghost Mode ntfy test")
