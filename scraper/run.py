#!/usr/bin/env python3
"""Nightly orchestrator for the Bioinfo Jobs Hub scraper.

Runs every configured source, merges results into data/jobs.json (keeping
each job's first-seen date stable across runs so "posted X days ago" is
meaningful), expires stale entries, and writes data/last_updated.json so
the site can show per-source status honestly instead of pretending
everything always works.

Usage: run from the repo root as `python scraper/run.py`.
"""

import json
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRAPER_DIR))  # so `from fetchutil import get` works inside sources/*

from sources import (  # noqa: E402
    euraxess,
    eurosciencejobs,
    jobrxiv,
    nature_careers,
    scilifelab,
)

SOURCES = [jobrxiv, nature_careers, euraxess, scilifelab, eurosciencejobs]
EXPIRY_DAYS = 45

JOBS_PATH = REPO_ROOT / "data" / "jobs.json"
META_PATH = REPO_ROOT / "data" / "last_updated.json"


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def today_iso():
    return datetime.now(timezone.utc).date().isoformat()


def normalise(raw_job, source_name, first_seen_lookup):
    """Fill in required fields, dropping anything without a usable URL/title."""
    url = (raw_job.get("url") or "").strip()
    title = (raw_job.get("title") or "").strip()
    if not url or not title:
        return None
    return {
        "title": title,
        "org": (raw_job.get("org") or "").strip(),
        "location": (raw_job.get("location") or "").strip(),
        "url": url,
        "source": source_name,
        "posted_date": raw_job.get("posted_date"),
        "first_seen": first_seen_lookup.get(url, today_iso()),
        "tags": raw_job.get("tags") or [],
    }


def run():
    existing_jobs = load_json(JOBS_PATH, [])
    existing_meta = load_json(META_PATH, {"sources": {}})

    existing_by_url = {j["url"]: j for j in existing_jobs}
    existing_by_source = {}
    for j in existing_jobs:
        existing_by_source.setdefault(j["source"], []).append(j)

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    final_jobs = []
    source_status = {}

    for module in SOURCES:
        name = module.SOURCE_NAME
        prev_info = existing_meta.get("sources", {}).get(name, {})
        try:
            raw_jobs = module.fetch()
            first_seen_lookup = {u: j["first_seen"] for u, j in existing_by_url.items() if j["source"] == name}
            normalised = [normalise(rj, name, first_seen_lookup) for rj in raw_jobs]
            normalised = [j for j in normalised if j is not None]

            final_jobs.extend(normalised)
            source_status[name] = {
                "status": "ok",
                "count": len(normalised),
                "last_success": now_iso,
            }
            print(f"[ok]   {name}: {len(normalised)} jobs")
        except Exception as exc:  # noqa: BLE001 -- one bad source must not kill the run
            print(f"[fail] {name}: {exc}")
            traceback.print_exc()

            # Fall back to the previous run's jobs for this source, but only
            # while they're still within the expiry window -- a source that
            # stays broken shouldn't keep showing indefinitely-stale listings.
            cutoff = (now - timedelta(days=EXPIRY_DAYS)).date().isoformat()
            fallback = [j for j in existing_by_source.get(name, []) if j["first_seen"] >= cutoff]
            final_jobs.extend(fallback)
            source_status[name] = {
                "status": "fail",
                "count": len(fallback),
                "last_success": prev_info.get("last_success"),
                "error": str(exc),
            }

    # Global safety-net expiry (covers any edge cases above).
    cutoff = (now - timedelta(days=EXPIRY_DAYS)).date().isoformat()
    final_jobs = [j for j in final_jobs if j.get("first_seen", today_iso()) >= cutoff]

    # De-dupe by URL across sources, keep the most recently seen instance.
    deduped = {}
    for j in final_jobs:
        deduped[j["url"]] = j
    final_jobs = sorted(
        deduped.values(),
        key=lambda j: j.get("posted_date") or j.get("first_seen") or "",
        reverse=True,
    )

    JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JOBS_PATH.write_text(json.dumps(final_jobs, indent=2, ensure_ascii=False), encoding="utf-8")
    META_PATH.write_text(
        json.dumps({"last_run": now_iso, "sources": source_status}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nWrote {len(final_jobs)} jobs total from {len(SOURCES)} sources.")


if __name__ == "__main__":
    run()
