# Instagram Post-Time Checker

Checks the exact posted time of a public Instagram reel/post URL.

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

## Why profile analysis (last 50 posts, views, best time range) isn't built yet

Confirmed by testing directly: Instagram blocks the post grid, timestamps,
and view counts for logged-out visitors at the server level (not just a UI
overlay — nothing is embedded in the page to scrape). So this can't be added
as a simple extension of the reel-checker above. It needs one of:

1. **A third-party scraping API** (Apify, RapidAPI Instagram scrapers, etc.) —
   most reliable, usually a paid service, you'd supply an API key.
2. **Instagram's official Graph API** — free and fully compliant, but only
   works for an Instagram **business/creator account you manage yourself**,
   not arbitrary public profiles.
3. **Manually collected data** — you paste in timestamps + view counts
   yourself (e.g. from Instagram's own creator insights), and a script just
   does the time-range math. No scraping involved.
4. **A logged-in automated browser session** — fragile (breaks whenever
   Instagram changes its UI or flags automation) and against Instagram's
   Terms of Service.

Once a data source is picked, the "best time range" analysis itself is
straightforward: bucket each post's timestamp (hour of day / day of week)
against its view count and rank buckets by average views.
