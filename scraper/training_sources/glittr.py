"""Glittr.org -- structured API of bioinformatics/data-science training
material hosted on GitHub, organised as category > topic > repository.

Verified live: https://glittr.org/api/list returns ~840 repositories
across 6 categories (Scripting & languages, Computational methods &
pipelines, Omics analysis, Reproducibility & data management, Statistics
& machine learning, Others). This is also the exact source that generates
the SIB Training Collection's own README (see their
scripts/create_collection_from_rest_api.py) -- so this scraper doesn't
just add to that list, it goes to where it actually comes from.

To keep the rendered page useful rather than an 800-item wall, only the
top MAX_PER_TOPIC repos per topic (by GitHub star count, with a MIN_STARS
floor) are kept.
"""

from fetchutil import get

SOURCE_NAME = "Glittr.org"
API_URL = "https://glittr.org/api/list"

MIN_STARS = 5
MAX_PER_TOPIC = 8


def fetch():
    resp = get(API_URL)
    data = resp.json()

    materials = []
    for category in data:
        cat_name = category.get("name") or "Other"
        for topic in category.get("topics", []):
            topic_name = topic.get("name") or "General"

            repos = [
                r for r in topic.get("repositories", [])
                if (r.get("stargazers") or 0) >= MIN_STARS and (r.get("website") or r.get("url"))
            ]
            repos.sort(key=lambda r: r.get("stargazers") or 0, reverse=True)

            for repo in repos[:MAX_PER_TOPIC]:
                title = repo.get("description") or repo.get("name") or "Untitled resource"
                author = (repo.get("author") or {}).get("display_name", "")

                materials.append({
                    "category": cat_name,
                    "topic": topic_name,
                    "title": title,
                    "url": repo.get("website") or repo.get("url"),
                    "repo_url": repo.get("url", ""),
                    "author": author,
                    "stars": repo.get("stargazers") or 0,
                })

    return materials
