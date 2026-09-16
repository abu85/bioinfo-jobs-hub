"""SciLifeLab -- careers listing page.

Verified live: https://www.scilifelab.se/career/ is static HTML with
direct links to each posting at https://www.scilifelab.se/career/<slug>/.
Sweden-specific, but SciLifeLab/NBIS postings are heavily bioinformatics-
and computational-biology-flavoured, so it's kept as a supplementary
source even though the site's overall scope is worldwide.
"""

import re

from bs4 import BeautifulSoup

from fetchutil import get

SOURCE_NAME = "SciLifeLab"
LIST_URL = "https://www.scilifelab.se/career/"

_POSTING_HREF = re.compile(r"^https://www\.scilifelab\.se/career/[^/]+/?$")


def fetch():
    resp = get(LIST_URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    seen_urls = set()
    for a in soup.find_all("a", href=_POSTING_HREF):
        href = a["href"].rstrip("/") + "/"
        if href == LIST_URL or href in seen_urls:
            continue
        seen_urls.add(href)

        title = a.get_text(strip=True)
        if not title:
            slug = href.rstrip("/").rsplit("/", 1)[-1]
            title = slug.replace("-", " ").title()

        jobs.append({
            "title": title,
            "org": "SciLifeLab",
            "location": "Sweden",
            "url": href,
            "posted_date": None,
            "tags": [],
        })

    return jobs
