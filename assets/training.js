/* Bioinfo Jobs Hub — training materials page.
   Reads data/training.json + data/training_last_updated.json (written
   nightly by scraper/run_training.py) and renders a grouped, searchable
   plain link list -- category > topic > links, not cards. */

(function () {
  "use strict";

  const state = { materials: [] };

  const $ = (sel) => document.querySelector(sel);
  const listEl = $("#material-list");
  const statusBarEl = $("#status-bar");
  const searchEl = $("#search");

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

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

  function renderStatusBar(meta) {
    if (!meta || !meta.last_run) {
      statusBarEl.innerHTML = "<span>No update data yet — the nightly scraper hasn't run in this repo.</span>";
      return;
    }
    const parts = [`<span>Feed last updated: <b>${escapeHtml(fmtRelative(meta.last_run))}</b></span>`];
    for (const [name, info] of Object.entries(meta.sources || {})) {
      const cls = info.status === "ok" ? "ok" : "fail";
      parts.push(`<span><span class="status-dot ${cls}"></span>${escapeHtml(name)} (${info.count ?? 0})</span>`);
    }
    statusBarEl.innerHTML = parts.join("");
  }

  function groupBy(list, keyFn) {
    const map = new Map();
    for (const item of list) {
      const key = keyFn(item);
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(item);
    }
    return map;
  }

  function render() {
    const query = searchEl.value.trim().toLowerCase();
    const filtered = query
      ? state.materials.filter((m) =>
          `${m.title} ${m.category} ${m.topic} ${m.author || ""}`.toLowerCase().includes(query))
      : state.materials;

    if (filtered.length === 0) {
      listEl.innerHTML = '<p class="empty-state">No materials match the current search.</p>';
      return;
    }

    const byCategory = groupBy(filtered, (m) => m.category || "Other");
    let html = "";
    for (const [category, catItems] of byCategory) {
      html += `<section class="category"><h2>${escapeHtml(category)}</h2>`;
      const byTopic = groupBy(catItems, (m) => m.topic || "General");
      for (const [topic, topicItems] of byTopic) {
        html += `<div class="topic-block"><h3 class="topic-title">${escapeHtml(topic)}</h3><ul class="material-list">`;
        for (const m of topicItems) {
          const metaBits = [];
          if (m.author) metaBits.push(escapeHtml(m.author));
          if (m.stars) metaBits.push(`★${m.stars}`);
          html += `<li class="material-item"><a href="${escapeHtml(m.url)}" target="_blank" rel="noopener">${escapeHtml(m.title)}</a>${metaBits.length ? `<span class="material-meta">${metaBits.join(" · ")}</span>` : ""}</li>`;
        }
        html += "</ul></div>";
      }
      html += "</section>";
    }
    listEl.innerHTML = html;
  }

  async function init() {
    try {
      const [dataRes, metaRes] = await Promise.all([
        fetch("data/training.json", { cache: "no-store" }),
        fetch("data/training_last_updated.json", { cache: "no-store" }),
      ]);
      state.materials = dataRes.ok ? await dataRes.json() : [];
      const meta = metaRes.ok ? await metaRes.json() : null;

      renderStatusBar(meta);

      if (state.materials.length === 0) {
        listEl.innerHTML = '<p class="empty-state">No scraped materials yet — the nightly scraper populates this list automatically. Check back after the first run, or see the hand-picked links above in the meantime.</p>';
      } else {
        render();
      }
    } catch (err) {
      listEl.innerHTML = `<p class="empty-state">Couldn't load training data (${escapeHtml(err.message)}).</p>`;
      statusBarEl.innerHTML = "<span>Status unavailable.</span>";
    }
  }

  searchEl.addEventListener("input", render);
  init();
})();
