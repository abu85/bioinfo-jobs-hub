# Bioinfo Jobs Hub

A static GitHub Pages site aggregating worldwide bioinformatics job postings, plus curated pages of training materials and bioinformatics infrastructure worldwide. The jobs feed updates itself automatically every night via GitHub Actions — no server, no database, no build step.

**Live site:** enable GitHub Pages (Settings → Pages → Deploy from branch → `main` / `/ (root)`) after pushing this repo, then it'll be at `https://<your-username>.github.io/<repo-name>/`.

## How it works

```
scraper/run.py  →  data/jobs.json + data/last_updated.json  →  index.html reads them client-side
        ↑ runs nightly via .github/workflows/update-jobs.yml (GitHub Actions cron)
```

No backend: the site is plain HTML/CSS/JS, and the only "dynamic" part is a JSON file that a scheduled GitHub Actions job overwrites and commits every night. GitHub Pages redeploys automatically on every push to `main`.

## Job sources

| Source | Method | Notes |
|---|---|---|
| [jobRxiv](https://jobrxiv.org/) | HTML (keyword search) | Their RSS feeds are served but empty; the search results page works fine. |
| [Nature Careers](https://www.nature.com/naturecareers/) | RSS | `jobsrss/?keywords=bioinformatics` — reliable, structured. |
| [EURAXESS](https://euraxess.ec.europa.eu/) | HTML (keyword search) | European research positions; anchored on the stable `/jobs/<id>` link pattern. |
| [SciLifeLab](https://www.scilifelab.se/career/) | HTML | Sweden-specific but heavily bioinformatics/computational-biology flavoured. |
| [EuroScienceJobs](https://www.eurosciencejobs.com/) | HTML (bioinformatics category) | |

**Deliberately not scraped: LinkedIn, Indeed, Academic Positions.** LinkedIn and Indeed explicitly prohibit automated scraping and run active anti-bot defenses (Indeed returns HTTP 403 to a plain fetch); Academic Positions sits behind a Cloudflare bot challenge. Automating against any of these would break repeatedly and risk the scraper's IP getting blocked. `index.html` links to pre-built searches on all three instead.

**NBIS** was tried and dropped: its `/about/work-with-us` page currently has no job listings in the static HTML (likely rendered client-side or hosted elsewhere) — nothing reliable to scrape there as of writing. Worth re-checking if their site changes.

Each source module in `scraper/sources/` is wrapped in a try/except by `scraper/run.py`, so one source breaking (a site redesign, a network blip) doesn't take down the whole nightly run — it falls back to that source's last-known-good jobs (up to the 45-day expiry window) and records the failure in `data/last_updated.json`, which the site surfaces honestly rather than silently.

## Adding a new source

1. Create `scraper/sources/<name>.py` with a `SOURCE_NAME` string and a `fetch()` function returning a list of dicts: `{title, org, location, url, posted_date, tags}` (all but `title`/`url` may be blank strings/None/[]).
2. Add it to the `SOURCES` list in `scraper/run.py`.
3. Test locally: `pip install -r scraper/requirements.txt && python scraper/run.py`, then check `data/jobs.json`.

## Local testing

Requires Python 3.9+ (this was developed without a local Python install available — the code is written and grounded against verified live HTML/RSS structure for each source, but hasn't been run end-to-end locally; test via `workflow_dispatch` in the Actions tab, or install Python locally and run `python scraper/run.py` from the repo root before relying on the schedule).

## Update schedule

Nightly at 23:00 UTC (00:00 CET). GitHub Actions cron is UTC-only and doesn't observe daylight saving, so this drifts to 01:00 CEST in summer. If exact midnight Europe/Stockholm year-round ever matters, the fix is to schedule two cron triggers (22:00 and 23:00 UTC) and have `run.py` check the current Europe/Stockholm hour via `zoneinfo` at the top, exiting early if it isn't the "right" one for the current season — not built now since it's unneeded precision for a once-a-night job.

## Pages

- `index.html` — the auto-updated jobs board.
- `training.html` — curated training-material links (hand-maintained; see [ELIXIR TeSS](https://tess.elixir-europe.org/) for a full searchable catalogue this deliberately doesn't try to replace).
- `infrastructure.html` — curated, representative (not exhaustive) directory of bioinformatics infrastructure worldwide: international bodies, national infrastructures, university core facilities.

Both curated pages are meant to grow — edit the HTML directly and add a `.res-card` block in the relevant category.
