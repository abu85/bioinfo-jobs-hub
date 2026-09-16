"""jobRxiv (jobrxiv.org) -- keyword-search HTML page.

Verified live: jobRxiv's own RSS feeds (/feed/ and /category/*/feed/) are
served but empty of <item> entries, so this scrapes the keyword-search
results page instead, which uses standard WP Job Manager markup
(`li.job_listing`) and is stable HTML (no JS rendering required).
"""

from bs4 import BeautifulSoup

from fetchutil import get

SOURCE_NAME = "jobRxiv"
SEARCH_URL = "https://jobrxiv.org/?search_keywords=bioinformatics"


def fetch():
    resp = get(SEARCH_URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    for li in soup.select("li.job_listing"):
        link = li.find("a", href=lambda h: h and "/job/" in h)
        if not link:
            continue
        url = link["href"].strip()
        title = link.get_text(strip=True)
        if not title:
            h3 = li.find("h3")
            title = h3.get_text(strip=True) if h3 else "Untitled listing"

        classes = li.get("class", [])
        region = next(
            (c.replace("job_listing_region-", "").replace("-", " ").title()
             for c in classes if c.startswith("job_listing_region-")),
            "",
        )
        tags = [
            c.replace("job_listing_category-", "")
            for c in classes if c.startswith("job_listing_category-")
        ]

        jobs.append({
            "title": title,
            "org": "",  # not reliably present in the list-view markup
            "location": region,
            "url": url,
            "posted_date": None,  # not exposed on the list view; first_seen tracks recency instead
            "tags": tags,
        })

    return jobs
