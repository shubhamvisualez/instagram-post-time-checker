#!/usr/bin/env python3
"""Web front-end for the Instagram post-time checker."""
import asyncio
import os

from flask import Flask, render_template, request

from core import build_post_result, classify_url, fetch_post_data, normalize_url, profile_message

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    raw_url = ""

    if request.method == "POST":
        raw_url = request.form.get("url", "").strip()
        if not raw_url:
            error = "Please paste an Instagram URL."
        else:
            url = normalize_url(raw_url)
            kind, ident = classify_url(url)
            if kind == "post":
                data = asyncio.run(fetch_post_data(url))
                result = build_post_result(url, data)
                if not result["ok"]:
                    error = result["error"]
                    result = None
            elif kind == "profile":
                error = profile_message(ident)
            else:
                error = "Could not recognize this as an Instagram profile or post/reel URL."

    return render_template("index.html", result=result, error=error, raw_url=raw_url)


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
