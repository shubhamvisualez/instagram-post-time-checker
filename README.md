# Instagram Post-Time Checker

Checks the exact posted time of a public Instagram reel/post URL.

**Live version:** https://instagram-post-time-checker.onrender.com (no setup needed — free tier, may take ~30s to wake up if idle)

## Setup

```bash
pip3 install playwright
python3 -m playwright install chromium
```

## Usage

```bash
python3 ig_time_checker.py "https://www.instagram.com/reel/DdMBBkBTbS_/"
```

Output:

```
Posted (UTC):   2026-09-12 12:45:38 UTC
Posted (local): 2026-09-12 18:15:38 IST
Day of week:    Saturday
Likes:          94
Comments:       16
```

Works for `/reel/<id>/` and `/p/<id>/` URLs. Query strings (like `?stkn=...`
share tokens) are stripped automatically.

## Why it needs a real browser, not a simple HTTP request

Instagram serves an empty page shell to plain HTTP clients (curl, `requests`)
and only renders post content via client-side JavaScript. This script drives
a real (headless) Chromium instance via [Playwright](https://playwright.dev/python/)
to let that JavaScript run, then reads the rendered `<time>` element — the
same thing a logged-out visitor sees in their own browser. It does not log in,
bypass any wall, or access anything a normal visitor couldn't see.
