# Bioinfo Jobs Hub

A static GitHub Pages site aggregating worldwide bioinformatics job postings, plus curated pages of training materials and bioinformatics infrastructure worldwide. The jobs feed updates itself automatically every night via GitHub Actions — no server, no database, no build step.

**Live site:** enable GitHub Pages (Settings → Pages → Deploy from branch → `main` / `/ (root)`) after pushing this repo, then it'll be at `https://<your-username>.github.io/<repo-name>/`.

## How it works

```
scraper/run.py  →  data/jobs.json + data/last_updated.json  →  index.html reads them client-side
        ↑ runs nightly via .github/workflows/update-jobs.yml (GitHub Actions cron)
```

No backend: the site is plain HTML/CSS/JS, and the only "dynamic" part is a JSON file that a scheduled GitHub Actions job overwrites and commits every night. GitHub Pages redeploys automatically on every push to `main`.

## Training materials

`training.html` is now auto-updated too, the same way the jobs board is:

```
scraper/run_training.py  →  data/training.json + data/training_last_updated.json  →  training.html reads them client-side
```

Source: [Glittr.org](https://glittr.org/api/list), a structured, actively maintained API of ~840 bioinformatics/data-science training repositories organised as category → topic → repository. It's also literally what generates the [SIB Training Collection](https://github.com/sib-swiss/training-collection)'s own README (see their `scripts/create_collection_from_rest_api.py`), so scraping it directly goes to the source rather than re-deriving from a page that itself re-derives from it.

To keep the page from being an 800-item wall, `scraper/training_sources/glittr.py` keeps only the top `MAX_PER_TOPIC` (8) repos per topic by GitHub star count, with a `MIN_STARS` (5) floor — both easy to tune in that file.

Run it the same way as the jobs scraper: `python scraper/run_training.py` from the repo root (after `pip install -r scraper/requirements.txt`). It's wired into the same nightly GitHub Actions workflow as a second step.

## Job sources

| Source | Method | Notes |
|---|---|---|
| [jobRxiv](https://jobrxiv.org/) | HTML (keyword search) | Their RSS feeds are served but empty; the search results page works fine. |
| [Nature Careers](https://www.nature.com/naturecareers/) | RSS | `jobsrss/?keywords=bioinformatics` — reliable, structured. |
| [EURAXESS](https://euraxess.ec.europa.eu/) | HTML (keyword search) | European research positions; anchored on the stable `/jobs/<id>` link pattern. |
| [SciLifeLab](https://www.scilifelab.se/career/) | HTML | Sweden-specific but heavily bioinformatics/computational-biology flavoured. |
| [EuroScienceJobs](https://www.eurosciencejobs.com/) | HTML (bioinformatics category) | |
| [bioinformatics.org](https://www.bioinformatics.org/jobs/) | HTML (forum-based board) | Its jobs board is a forum; title/date are scraped from the thread listing. |
| [Max Planck Society](https://www.mpg.de/jobboard) | RSS, keyword-filtered | Feed covers every field the Society works in, not just biology, so entries are filtered client-side against a bioinformatics/computational-biology keyword list rather than trusted as pre-filtered. |

**Deliberately not scraped: LinkedIn, Indeed, Academic Positions, PostdocJobs.com.** All explicitly prohibit automated scraping and/or run active anti-bot defenses (Indeed and PostdocJobs.com return HTTP 403 to a plain fetch; Academic Positions sits behind a Cloudflare bot challenge). Automating against these would break repeatedly and risk the scraper's IP getting blocked. `index.html` links to pre-built searches on LinkedIn/Indeed/Glassdoor instead.

**Tried and dropped, worth re-checking later:**
- **NBIS** — `/about/work-with-us` currently has no job listings in the static HTML (likely rendered client-side or hosted elsewhere).
- **EMBL-EBI, Wellcome Sanger** — both redirect their actual listings to Workday-hosted ATS pages (`*.wd103.myworkdayjobs.com`), which are JS-rendered and not reliably scrapeable with a plain HTTP request. The same is likely true of other large institutes on Workday (e.g. Broad Institute, which returned HTTP 403 directly).
- **Academic Jobs Online** — has real static-HTML listings, but its field/category codes aren't self-explanatory in the page source and the one guessed (`field=13`) turned out to be physics/math faculty positions, not life sciences. Worth adding once the correct bioinformatics/computational-biology field code is identified.
- **HigherEdJobs** — returned a near-empty 212-byte response, suggesting the real content loads via JS.

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
- `training.html` — the auto-updated training-materials list (see "Training materials" above; source is Glittr.org, not hand-maintained).
- `infrastructure.html` — curated, representative (not exhaustive) directory of bioinformatics infrastructure worldwide: international bodies, national infrastructures, university core facilities. Still hand-maintained — edit the HTML directly and add a `.res-card` block in the relevant category.
