"""EuroScienceJobs -- bioinformatics category listing page.

Verified live: static HTML, job links of the form
/job_display/<id>/<Title_With_Underscores>.
"""

import re

from bs4 import BeautifulSoup

from fetchutil import get

SOURCE_NAME = "EuroScienceJobs"
LIST_URL = "https://www.eurosciencejobs.com/job_search/category/bioinformatics"
BASE_URL = "https://www.eurosciencejobs.com"

_JOB_HREF = re.compile(r"^/job_display/\d+/")


def fetch():
    resp = get(LIST_URL)
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
            # fall back to the URL slug, e.g. ".../Principal_Scientist_X_Ghent_Belgium"
            slug = href.rstrip("/").rsplit("/", 1)[-1]
            title = slug.replace("_", " ")

        jobs.append({
            "title": title,
            "org": "",
            "location": "",
            "url": BASE_URL + href,
            "posted_date": None,
            "tags": [],
        })

    return jobs
