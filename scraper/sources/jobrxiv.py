"""jobRxiv (jobrxiv.org) -- keyword-search HTML page.

Verified live: jobRxiv's own RSS feeds (/feed/ and /category/*/feed/) are
served but empty of <item> entries, so this scrapes the keyword-search
results page instead (standard WP Job Manager markup).

Important quirk found from a real production run: each `li.job_listing`
wraps its ENTIRE card -- title, meta, and description excerpt -- in a
single <a>. Taking that link's whole get_text() (an earlier version of
this file did) produces a title string with the job type, tags, company,
location and description all run together with no separators. The title
is actually the <h4>'s own direct text node (its first child, before the
nested "Full-time"-style <span>); org/location/date live in their own
`.ws-meta-*` spans and a `<time datetime="...">` attribute.
"""

from bs4 import BeautifulSoup, NavigableString

from fetchutil import get

SOURCE_NAME = "jobRxiv"
SEARCH_URL = "https://jobrxiv.org/?search_keywords=bioinformatics"


def _title_text(h4):
    if not h4:
        return ""
    # first direct text node only -- skips the nested job-type span
    for child in h4.children:
        if isinstance(child, NavigableString) and child.strip():
            return child.strip()
    return h4.get_text(strip=True)


def _meta_text(li, css_class):
    el = li.select_one(css_class)
    if not el:
        return ""
    # drop the leading Font Awesome <i> icon, keep the rest
    for icon in el.find_all("i"):
        icon.decompose()
    return el.get_text(strip=True)


def fetch():
    resp = get(SEARCH_URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    for li in soup.select("li.job_listing"):
        link = li.find("a", href=lambda h: h and "/job/" in h)
        if not link:
            continue

        title = _title_text(link.find("h4"))
        if not title:
            continue

        time_el = link.find("time")
        posted_date = time_el["datetime"].strip() if time_el and time_el.get("datetime") else None

        tags = [kw.get_text(strip=True) for kw in link.select(".job-keyword")]

        jobs.append({
            "title": title,
            "org": _meta_text(link, ".ws-meta-company-name"),
            "location": _meta_text(link, ".ws-meta-job-location"),
            "url": link["href"].strip(),
            "posted_date": posted_date,
            "tags": tags,
        })

    return jobs
