#!/usr/bin/env python3
"""
Instagram post-time checker (CLI).

Usage:
    python3 ig_time_checker.py <instagram-url> [timezone]

- Reel / post URL  -> prints the exact posted date/time (UTC + a timezone of
                       your choice, default Asia/Kolkata/IST), likes and comments.
- Profile URL      -> explains why bulk profile analysis (last 50 posts + view
                       counts + best-time-range) isn't available yet.

[timezone] is any IANA name, e.g. America/New_York, Europe/London, UTC.

Requires a real browser engine (Instagram serves an empty shell to plain HTTP
clients and only renders content via JavaScript) so this uses Playwright.
Setup:
    pip3 install playwright
    python3 -m playwright install chromium

A hosted web version (no setup needed) is linked in README.md.
"""
import asyncio
import sys

from core import DEFAULT_TZ, build_post_result, classify_url, fetch_post_data, normalize_url, profile_message


def print_post_result(result: dict):
    print(f"\nURL: {result['url']}")
    if not result["ok"]:
        print(result["error"])
        return

    print(f"Posted (UTC):          {result['posted_utc']}")
    print(f"Posted ({result['tz_name']}): {result['posted_tz']}")
    print(f"Day of week:           {result['day_of_week']}")
    if result.get("likes"):
        print(f"Likes:          {result['likes']}")
    if result.get("comments"):
        print(f"Comments:       {result['comments']}")
    print(
        "\nNote: Instagram does not expose view/play counts to logged-out "
        "visitors, so that figure isn't available here."
    )


async def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python3 ig_time_checker.py <instagram-url> [timezone]")
        sys.exit(1)

    url = normalize_url(sys.argv[1])
    tz_name = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_TZ
    kind, ident = classify_url(url)

    if kind == "post":
        data = await fetch_post_data(url)
        print_post_result(build_post_result(url, data, tz_name=tz_name))
    elif kind == "profile":
        print(f"\nURL: {url}")
        print(profile_message(ident))
    else:
        print("Could not recognize this as an Instagram profile or post/reel URL.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
