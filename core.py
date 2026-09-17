"""Shared logic for checking an Instagram reel/post's posted time.

Used by both the CLI (ig_time_checker.py) and the web app (app.py).
"""
import re
from datetime import datetime
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


def normalize_url(raw_url: str) -> str:
    return raw_url.strip().split("?")[0].rstrip("/") + "/"


async def fetch_post_data(url: str) -> dict:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = await browser.new_page(user_agent=USER_AGENT)
        await page.goto(url, wait_until="networkidle", timeout=30000)

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


def build_post_result(url: str, data: dict) -> dict:
    """Turn raw scrape data into a plain-dict result usable by CLI or web output."""
    t = data.get("time")
    if not t or not t.get("datetime"):
        return {
            "ok": False,
            "url": url,
            "error": (
                "Could not read the posted time. Instagram may have changed its "
                "page structure, or this content requires login to view (private "
                "account, age-restricted, or removed post)."
            ),
        }

    dt_utc = datetime.fromisoformat(t["datetime"].replace("Z", "+00:00"))
    dt_local = dt_utc.astimezone()

    return {
        "ok": True,
        "url": url,
        "posted_utc": dt_utc.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "posted_local": dt_local.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "day_of_week": dt_utc.strftime("%A"),
        "likes": data.get("likes"),
        "comments": data.get("comments"),
    }


def profile_message(username: str) -> str:
    return (
        f"This is a profile page (@{username}), not a single post/reel.\n\n"
        "Best-time-range analysis needs the last ~50 posts' timestamps + view "
        "counts, but Instagram hides that entirely from logged-out visitors "
        "(the profile grid is blocked behind a login wall server-side, no data "
        "is embedded in the page for scraping).\n\n"
        "This feature needs one of:\n"
        "1. A third-party scraping API (e.g. Apify, RapidAPI Instagram scrapers)\n"
        "2. Instagram's official Graph API (only works for your own business/"
        "creator account, not arbitrary public profiles)\n"
        "3. Manually pasted data (timestamps + views you collect yourself)\n"
        "4. A logged-in browser session (fragile, against Instagram's ToS)"
    )
