"""Nature Careers -- RSS search feed.

Verified live: https://www.nature.com/naturecareers/jobsrss/?keywords=<q>
returns a proper RSS 2.0 feed with <item> entries (confirmed 20 items /
154 total results for "bioinformatics"). Each item's <description> is
free text, roughly: "<salary>:\n\n<org>:\n<title details>\n<location>\n" --
parsed heuristically below and left blank on anything that doesn't fit,
rather than guessed at.
"""

import feedparser

from fetchutil import get

SOURCE_NAME = "Nature Careers"
FEED_URL = "https://www.nature.com/naturecareers/jobsrss/?keywords=bioinformatics"


def _parse_description(desc):
    lines = [ln.strip() for ln in (desc or "").split("\n") if ln.strip()]
    org = lines[1].rstrip(":") if len(lines) >= 2 else ""
    location = lines[-1] if len(lines) >= 3 else ""
    return org, location


def fetch():
    resp = get(FEED_URL)
    parsed = feedparser.parse(resp.content)
    if parsed.bozo and not parsed.entries:
        raise RuntimeError(f"Nature Careers feed did not parse: {parsed.bozo_exception}")

    jobs = []
    for entry in parsed.entries:
        org, location = _parse_description(entry.get("description", ""))
        posted = None
        if entry.get("published_parsed"):
            import time
            posted = time.strftime("%Y-%m-%d", entry.published_parsed)

        jobs.append({
            "title": entry.get("title", "Untitled listing"),
            "org": org,
            "location": location,
            "url": entry.get("link", ""),
            "posted_date": posted,
            "tags": [],
        })

    return jobs
