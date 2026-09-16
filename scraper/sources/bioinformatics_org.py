"""bioinformatics.org -- jobs board (forum-based).

Verified live: static HTML, no JS rendering needed. Postings are forum
threads (`li.tree-node`): title + link live under `.node-title a`, and the
posting date is the last `<span>` inside `.node-header` (e.g. "August 29,
2026"). This board is not filtered by keyword -- as its name suggests it's
already bioinformatics-specific.
"""

from dateutil import parser as dateparser
from bs4 import BeautifulSoup

from fetchutil import get

SOURCE_NAME = "bioinformatics.org"
LIST_URL = "https://www.bioinformatics.org/jobs/"


def _parse_date(node):
    spans = node.select(".node-header span")
    if not spans:
        return None
    try:
        return dateparser.parse(spans[-1].get_text(strip=True)).date().isoformat()
    except (ValueError, OverflowError):
        return None


def fetch():
    resp = get(LIST_URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    for node in soup.select("li.tree-node"):
        title_link = node.select_one(".node-title a")
        if not title_link or not title_link.get("href"):
            continue

        jobs.append({
            "title": title_link.get_text(strip=True),
            "org": "",  # embedded in the free-text posting body, not reliably structured
            "location": "",
            "url": title_link["href"],
            "posted_date": _parse_date(node),
            "tags": [],
        })

    return jobs
