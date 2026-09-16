#!/usr/bin/env python3
"""Nightly orchestrator for the training-materials feed.

Mirrors run.py's structure (per-source try/except, fall back to the
previous run's output for a source that breaks, honest status reporting)
but is a separate script from the jobs scraper since training materials
are a conceptually different feed with different freshness needs -- and
keeping them separate means a broken jobs source can't affect the
training page or vice versa.

Usage: run from the repo root as `python scraper/run_training.py`.
"""

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRAPER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRAPER_DIR))

from training_sources import glittr  # noqa: E402

SOURCES = [glittr]

TRAINING_PATH = REPO_ROOT / "data" / "training.json"
META_PATH = REPO_ROOT / "data" / "training_last_updated.json"


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def run():
    existing_meta = load_json(META_PATH, {"sources": {}})
    existing_materials = load_json(TRAINING_PATH, [])

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    all_materials = []
    source_status = {}

    for module in SOURCES:
        name = module.SOURCE_NAME
        prev_info = existing_meta.get("sources", {}).get(name, {})
        try:
            items = module.fetch()
            for item in items:
                item["source"] = name
            all_materials.extend(items)
            source_status[name] = {"status": "ok", "count": len(items), "last_success": now_iso}
            print(f"[ok]   {name}: {len(items)} materials")
        except Exception as exc:  # noqa: BLE001 -- one bad source must not kill the run
            print(f"[fail] {name}: {exc}")
            traceback.print_exc()

            fallback = [m for m in existing_materials if m.get("source") == name]
            all_materials.extend(fallback)
            source_status[name] = {
                "status": "fail",
                "count": len(fallback),
                "last_success": prev_info.get("last_success"),
                "error": str(exc),
            }

    # De-dupe by URL, keep the highest-star instance if a URL appears twice.
    by_url = {}
    for m in all_materials:
        existing = by_url.get(m["url"])
        if existing is None or m.get("stars", 0) > existing.get("stars", 0):
            by_url[m["url"]] = m
    deduped = sorted(
        by_url.values(),
        key=lambda m: (m.get("category", ""), m.get("topic", ""), -m.get("stars", 0)),
    )

    TRAINING_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRAINING_PATH.write_text(json.dumps(deduped, indent=2, ensure_ascii=False), encoding="utf-8")
    META_PATH.write_text(
        json.dumps({"last_run": now_iso, "sources": source_status}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nWrote {len(deduped)} training materials from {len(SOURCES)} source(s).")


if __name__ == "__main__":
    run()
