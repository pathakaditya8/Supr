"""Optional self-ping so a free Render instance is not put to sleep after 15 idle minutes.

Render stops a free web service that receives no incoming web traffic for 15 minutes. When KEEP_ALIVE is
"true", the app requests its own public /api/health address every 10 minutes. The request goes out through
Render's public address, so it counts as incoming traffic. Render sets RENDER_EXTERNAL_URL automatically.

Limits: a free service has 750 instance-hours a month, enough for one service running all month. If the
service crashes or is redeployed it restarts and resumes pinging. It does not keep a sleeping service awake;
the first visit after any restart can still be slow.
"""
import asyncio
import logging
import os
import urllib.request

log = logging.getLogger("supr.keepalive")
INTERVAL_SECONDS = 600


def target_url():
    if os.getenv("KEEP_ALIVE", "").strip().lower() not in {"1", "true", "yes"}: return None
    base = os.getenv("KEEP_ALIVE_URL") or os.getenv("RENDER_EXTERNAL_URL", "")
    return base.rstrip("/") + "/api/health" if base.startswith("https://") else None


def _ping(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as r:  # noqa: S310  (https URL checked in target_url)
            return r.status
    except OSError as exc:
        log.warning("keep-alive ping failed: %s", exc)


async def run(url, interval=INTERVAL_SECONDS):
    await asyncio.sleep(interval)
    while True:
        await asyncio.to_thread(_ping, url)
        await asyncio.sleep(interval)
