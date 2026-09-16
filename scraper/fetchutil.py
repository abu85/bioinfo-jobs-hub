"""Shared HTTP helper for source scrapers: a browser-like User-Agent and a
short timeout, so one hanging site can't stall the whole nightly run.

Named `fetchutil` rather than `http` deliberately -- a same-named local
module would shadow Python's stdlib `http` package (which `requests`
itself depends on) for anything importing it from this directory.
"""

import requests

HEADERS = {
    # A plain custom bot UA got a clean 403 from EURAXESS specifically when
    # run from GitHub Actions' runner IP (worked fine testing from a normal
    # network) -- this fuller, ordinary-browser-shaped header set is the
    # standard fix for basic bot-detection, but there's no guarantee it
    # clears whatever EURAXESS is actually checking (IP reputation,
    # datacenter-range blocking, etc. wouldn't be fixed by headers alone).
    # If EURAXESS keeps failing after this, treat it like NBIS/EBI: not
    # reliably scrapeable, and drop it rather than keep fighting it.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 20


def get(url, **kwargs):
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, **kwargs)
    resp.raise_for_status()
    return resp
