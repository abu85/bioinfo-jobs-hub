"""EURAXESS -- keyword-search HTML page.

Verified live: https://euraxess.ec.europa.eu/jobs/search?keywords=<q>
returns static HTML (no JS rendering needed) with job detail links of the
form /jobs/<id>. The surrounding result-card markup uses the EU's ECL
component classes, which are more likely to change than the /jobs/<id>
link pattern -- so this anchors only on that link pattern and takes the
link text as the title, degrading gracefully (blank org/location) rather
than guessing at a specific card structure that may shift.
"""

import re

from bs4 import BeautifulSoup

from fetchutil import get

SOURCE_NAME = "EURAXESS"
SEARCH_URL = "https://euraxess.ec.europa.eu/jobs/search?keywords=bioinformatics"
BASE_URL = "https://euraxess.ec.europa.eu"

_JOB_HREF = re.compile(r"^/jobs/\d+$")


def fetch():
    resp = get(SEARCH_URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    seen_urls = set()
    for a in soup.find_all("a", href=_JOB_HREF):
        href = a["href"]
        if href in seen_urls:
            continue
        seen_urls.add(href)

        title = a.get_text(strip=True)
        if not title:
            continue

        jobs.append({
            "title": title,
            "org": "",
            "location": "",
            "url": BASE_URL + href,
            "posted_date": None,
            "tags": ["EU research position"],
        })

    return jobs
