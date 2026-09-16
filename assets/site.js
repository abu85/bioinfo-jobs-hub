/* Bioinfo Jobs Hub — client-side rendering for the jobs board.
   Reads data/jobs.json and data/last_updated.json (both written nightly
   by scraper/run.py via GitHub Actions) and renders/filters them. */

(function () {
  "use strict";

  const state = { jobs: [], sources: new Set() };

  const $ = (sel) => document.querySelector(sel);
  const jobListEl = $("#job-list");
  const statusBarEl = $("#status-bar");
  const footerUpdatedEl = $("#footer-updated");
  const searchEl = $("#search");
  const sourceSelectEl = $("#filter-source");
  const recencySelectEl = $("#filter-recency");

  function daysAgo(isoDate) {
    if (!isoDate) return null;
    const then = new Date(isoDate).getTime();
    if (Number.isNaN(then)) return null;
    return Math.floor((Date.now() - then) / 86400000);
  }

  function fmtRelative(isoDate) {
    const d = daysAgo(isoDate);
    if (d === null) return "date unknown";
    if (d <= 0) return "today";
    if (d === 1) return "1 day ago";
    return `${d} days ago`;
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function renderStatusBar(meta) {
    if (!meta) {
      statusBarEl.innerHTML = "<span>No update data yet — the nightly scraper hasn't run in this repo.</span>";
      return;
    }
    const parts = [`<span>Feed last updated: <b>${escapeHtml(fmtRelative(meta.last_run))}</b></span>`];
    const sources = meta.sources || {};
    for (const [name, info] of Object.entries(sources)) {
      const cls = info.status === "ok" ? "ok" : (daysAgo(info.last_success) !== null && daysAgo(info.last_success) <= 3 ? "stale" : "fail");
      parts.push(
        `<span><span class="status-dot ${cls}"></span>${escapeHtml(name)} (${info.count ?? 0})</span>`
      );
    }
    statusBarEl.innerHTML = parts.join("");
    footerUpdatedEl.textContent = `Data last updated: ${fmtRelative(meta.last_run)}`;
  }

  function populateSourceFilter() {
    const sorted = Array.from(state.sources).sort();
    for (const s of sorted) {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      sourceSelectEl.appendChild(opt);
    }
  }

  function jobMatches(job, query, sourceFilter, recencyFilter) {
    if (sourceFilter && job.source !== sourceFilter) return false;
    if (recencyFilter) {
      const d = daysAgo(job.posted_date || job.first_seen);
      if (d === null || d > Number(recencyFilter)) return false;
    }
    if (query) {
      const hay = `${job.title} ${job.org} ${(job.tags || []).join(" ")}`.toLowerCase();
      if (!hay.includes(query.toLowerCase())) return false;
    }
    return true;
  }

  function renderJobs() {
    const query = searchEl.value.trim();
    const sourceFilter = sourceSelectEl.value;
    const recencyFilter = recencySelectEl.value;

    const filtered = state.jobs
      .filter((j) => jobMatches(j, query, sourceFilter, recencyFilter))
      .sort((a, b) => new Date(b.posted_date || b.first_seen || 0) - new Date(a.posted_date || a.first_seen || 0));

    if (filtered.length === 0) {
      jobListEl.innerHTML = '<p class="empty-state">No jobs match the current filters.</p>';
      return;
    }

    jobListEl.innerHTML = filtered.map((job) => `
      <div class="job-card">
        <a class="job-link" href="${escapeHtml(job.url)}" target="_blank" rel="noopener">
          <h3 class="job-title">${escapeHtml(job.title)}</h3>
        </a>
        <p class="job-org">${escapeHtml(job.org)}${job.location ? " · " + escapeHtml(job.location) : ""}</p>
        <div class="job-meta">
          <span class="tag">${escapeHtml(job.source)}</span>
          ${(job.tags || []).map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join("")}
        </div>
        <div class="job-when">${escapeHtml(fmtRelative(job.posted_date || job.first_seen))}</div>
      </div>
    `).join("");
  }

  async function init() {
    try {
      const [jobsRes, metaRes] = await Promise.all([
        fetch("data/jobs.json", { cache: "no-store" }),
        fetch("data/last_updated.json", { cache: "no-store" }),
      ]);
      state.jobs = jobsRes.ok ? await jobsRes.json() : [];
      const meta = metaRes.ok ? await metaRes.json() : null;

      state.jobs.forEach((j) => j.source && state.sources.add(j.source));
      populateSourceFilter();
      renderStatusBar(meta);

      if (state.jobs.length === 0) {
        jobListEl.innerHTML = '<p class="empty-state">No jobs yet — the nightly scraper populates this feed automatically. Check back after the first run.</p>';
      } else {
        renderJobs();
      }
    } catch (err) {
      jobListEl.innerHTML = `<p class="empty-state">Couldn't load job data (${escapeHtml(err.message)}).</p>`;
      statusBarEl.innerHTML = "<span>Status unavailable.</span>";
    }
  }

  searchEl.addEventListener("input", renderJobs);
  sourceSelectEl.addEventListener("change", renderJobs);
  recencySelectEl.addEventListener("change", renderJobs);

  init();
})();
