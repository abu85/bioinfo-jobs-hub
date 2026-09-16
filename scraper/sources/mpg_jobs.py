"""Max Planck Society -- jobs RSS feed, keyword-filtered.

Verified live: https://www.mpg.de/feeds/jobs.rss is a clean, well-formed
RSS feed (confirmed 30 current items). It has no keyword-search parameter
though -- it's every open position across the whole Max Planck Society
(physics, chemistry, biology, humanities, everything) -- so this filters
to bioinformatics-relevant postings client-side by keyword match against
title + description, the same way a human would scan the list.
"""

import time

import feedparser

from fetchutil import get

SOURCE_NAME = "Max Planck Society"
FEED_URL = "https://www.mpg.de/feeds/jobs.rss"

KEYWORDS = (
    "bioinformatic", "computational biology", "genomic", "transcriptom",
    "metagenom", "computational genetics", "data science", "biostatistic",
    "systems biology", "machine learning", "sequencing", "proteomic",
)


def _is_relevant(title, description):
    hay = f"{title} {description}".lower()
    return any(kw in hay for kw in KEYWORDS)


def fetch():
    resp = get(FEED_URL)
    parsed = feedparser.parse(resp.content)
    if parsed.bozo and not parsed.entries:
        raise RuntimeError(f"Max Planck jobs feed did not parse: {parsed.bozo_exception}")

    jobs = []
    for entry in parsed.entries:
        title = entry.get("title", "")
        description = entry.get("description", "")
        if not _is_relevant(title, description):
            continue

        posted = None
        if entry.get("published_parsed"):
            posted = time.strftime("%Y-%m-%d", entry.published_parsed)

        jobs.append({
            "title": title or "Untitled listing",
            "org": "Max Planck Society",
            "location": "Germany",
            "url": entry.get("link", ""),
            "posted_date": posted,
            "tags": [],
        })

    return jobs
