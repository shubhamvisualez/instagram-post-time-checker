#!/usr/bin/env python3
"""
Instagram post-time checker.

Usage:
    python3 ig_time_checker.py <instagram-url>

- Reel / post URL  -> prints the exact posted date/time (UTC + your local time),
                       likes and comments.
- Profile URL      -> explains why bulk profile analysis (last 50 posts + view
                       counts + best-time-range) isn't available yet: Instagram
                       blocks that data for logged-out visitors. See README.md
                       for the options to unlock it.

Requires a real browser engine (Instagram serves an empty shell to plain HTTP
clients and only renders content via JavaScript) so this uses Playwright.
Setup:
    pip3 install playwright
    python3 -m playwright install chromium
"""
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

from playwright.async_api import async_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def classify_url(url: str):
    path = urlparse(url).path.strip("/")
    parts = path.split("/")
    if parts and parts[0] in ("reel", "p", "reels"):
        return "post", parts[1] if len(parts) > 1 else None
    if parts and parts[0]:
        return "profile", parts[0]
    return "unknown", None


async def fetch_post_data(url: str) -> dict:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=USER_AGENT)
        await page.goto(url, wait_until="networkidle", timeout=30000)

        # Instagram renders a <time datetime="..."> element on post/reel pages
        # once hydrated, even for logged-out visitors.
        try:
            await page.wait_for_selector("time", timeout=15000)
        except Exception:
            pass

        time_data = await page.evaluate(
            """() => {
                const t = document.querySelector('time');
                return t ? {datetime: t.getAttribute('datetime'), title: t.getAttribute('title')} : null;
            }"""
        )

        description = await page.evaluate(
            """() => {
                const m = document.querySelector('meta[name="description"]');
                return m ? m.getAttribute('content') : null;
            }"""
        )

        await browser.close()

    likes = comments = None
    if description:
        m = re.search(r"([\d,]+)\s+likes?,\s+([\d,]+)\s+comments?", description)
        if m:
            likes = m.group(1)
            comments = m.group(2)

    return {"time": time_data, "description": description, "likes": likes, "comments": comments}


def print_post_result(url: str, data: dict):
    print(f"\nURL: {url}")
    t = data.get("time")
    if not t or not t.get("datetime"):
        print("Could not read the posted time. Instagram may have changed its page")
        print("structure, or this content requires login to view (private account,")
        print("age-restricted, or removed post).")
        return

    dt_utc = datetime.fromisoformat(t["datetime"].replace("Z", "+00:00"))
    dt_local = dt_utc.astimezone()

    print(f"Posted (UTC):   {dt_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Posted (local): {dt_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Day of week:    {dt_utc.strftime('%A')}")
    if data.get("likes"):
        print(f"Likes:          {data['likes']}")
    if data.get("comments"):
        print(f"Comments:       {data['comments']}")
    print(
        "\nNote: Instagram does not expose view/play counts to logged-out "
        "visitors, so that figure isn't available here."
    )


def print_profile_message(url: str, username: str):
    print(f"\nURL: {url}")
    print(f"This is a profile page (@{username}), not a single post/reel.")
    print(
        "\nBest-time-range analysis needs the last ~50 posts' timestamps + view\n"
        "counts, but Instagram hides that entirely from logged-out visitors\n"
        "(confirmed: the profile grid is blocked behind a login wall server-side,\n"
        "no data is embedded in the page for scraping).\n"
        "\nThis feature is intentionally not implemented yet - it needs one of:\n"
        "  1. A third-party scraping API (e.g. Apify, RapidAPI Instagram scrapers)\n"
        "  2. Instagram's official Graph API (only works for YOUR OWN business/\n"
        "     creator account, not arbitrary public profiles)\n"
        "  3. Manually pasted data (timestamps + views you collect yourself)\n"
        "  4. A logged-in browser session (fragile, against Instagram's ToS)\n"
        "\nSee README.md for details. Pick one and this script can be extended."
    )


async def main():
    if len(sys.argv) != 2:
        print("Usage: python3 ig_time_checker.py <instagram-url>")
        sys.exit(1)

    url = sys.argv[1].split("?")[0].rstrip("/") + "/"
    kind, ident = classify_url(url)

    if kind == "post":
        data = await fetch_post_data(url)
        print_post_result(url, data)
    elif kind == "profile":
        print_profile_message(url, ident)
    else:
        print("Could not recognize this as an Instagram profile or post/reel URL.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
