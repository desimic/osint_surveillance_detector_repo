# Ghost Mode OSINT Stack (with OpenCanary)

This package deploys:
- SpiderFoot (OSINT engine)
- ntfy (push notifications)
- Tailscale (private global access)
- OpenCanary (honeypot) + real-time watcher wired to ntfy

## Quick Start
```bash
cp .env.example .env
# edit .env with your values (TS_AUTHKEY, NTFY_*)
docker compose up -d --build
```

## Services
- SpiderFoot → http://localhost:5001 (or your Tailscale IP / MagicDNS)
- ntfy → http://localhost
- OpenCanary ports (tailnet-only recommended):
  - HTTP 8081
  - FTP 2121

## Alerts
- `alerts` service: sends a startup test message to your ntfy topic
- `canary_watcher`: tails `/logs/opencanary/opencanary.log` and pushes every hit to ntfy
