"""Shared HTTP helper for source scrapers: a browser-like User-Agent and a
short timeout, so one hanging site can't stall the whole nightly run.

Named `fetchutil` rather than `http` deliberately -- a same-named local
module would shadow Python's stdlib `http` package (which `requests`
itself depends on) for anything importing it from this directory.
"""

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BioinfoJobsHubBot/1.0; "
        "+https://github.com/) bioinfo-jobs-hub-scraper"
    )
}
TIMEOUT = 20


def get(url, **kwargs):
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, **kwargs)
    resp.raise_for_status()
    return resp
