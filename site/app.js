// BAM Extraction Benchmark dashboard. Plain JavaScript, no build step, works offline.
"use strict";

const TARGETS = { open: 60, closed: 100 }; // annotated pages planned for the Nov 30 release
const METRICS = [
  ["overall", "Overall", "Mean of E1, E2 and E3"],
  ["e1_text", "E1 Text", "1 minus normalised edit distance"],
  ["e2_table_teds", "E2 Tables", "TEDS, structure and cell content"],
  ["e2_table_teds_struct", "E2 Structure", "TEDS, structure only"],
  ["e3_formula", "E3 Formulas", "1 minus normalised edit distance on LaTeX"],
  ["numbers_recall", "Numbers", "Share of the printed numbers that the output holds digit for digit. Not part of Overall"],
  ["e5_record_f1", "E5 Records", "Exact-record F1 on measurement rows"],
];

// Speed and cost columns: lower is better. Cost is worked out from the GPU slice and an hourly price.
const COSTS = [
  ["seconds_per_page", "Sec / page", "Wall time of the run divided by pages, model already loaded", (x) => x.toFixed(1)],
  ["eur_per_1000_pages", "€ / 1k pages", "Share of an A100 the slice uses × hours per 1,000 pages × hourly price", (x) => x.toFixed(2)],
  ["output_tokens_per_page", "Tokens / page", "Tokens the model wrote per page. Recorded from runs after Nov 3", (x) => String(x)],
];

// Views kept in pages.js register here under the first part of their route.
const PAGES = {};
const $app = document.getElementById("app");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pct = (x) => (x === null || x === undefined ? "—" : (100 * x).toFixed(1));
const store = {
  get(k, d) { try { return localStorage.getItem(k) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
};

// A hosted copy (GitLab Pages) has no server behind it: it reads the JSON files that
// `bambench export-site` wrote, and everything that changes data is switched off.
const STATIC = window.BAMBENCH_STATIC || null;
async function api(path, opts = {}) {
  if (STATIC) {
    if (opts.method && opts.method !== "GET") throw new Error("This copy is read-only. Use the dashboard on the BAM cluster to change data.");
    const r = await fetch("api/" + path.split("?")[0] + ".json");
    if (!r.ok) throw new Error("Not part of this read-only copy");
    return r.json();
  }
  const r = await fetch("/api/" + path, opts);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.error || r.statusText);
  return body;
}
function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => t.classList.remove("show"), 2600);
}
const trackPill = (t) => `<span class="pill ${t}">${t === "closed" ? "closed · confidential" : "open"}</span>`;

// ---------- Overview ----------
async function overview() {
  const [ov, lb] = await Promise.all([api("overview"), api("leaderboard")]);
  const tile = (t) => {
    const s = ov.tracks[t], target = TARGETS[t];
    if (!s) return `<div class="tile"><div class="k">${t} track</div><div class="v"><span class="small muted">not shown in this copy</span></div>
      <div class="s">Its page counts appear once the first closed-track results are published with <code>export-closed</code>.</div></div>`;
    const c = Math.min(100, (100 * s.pages_checked) / target), d = Math.min(100 - c, (100 * s.pages_draft) / target);
    return `<div class="tile"><div class="k">${t} track</div>
      <div class="v">${s.pages_checked + s.pages_draft} <span class="small muted">/ ${target} pages annotated</span></div>
      <div class="bar"><span class="checked" style="width:${c}%"></span><span class="draft" style="width:${d}%"></span></div>
      <div class="s">${s.documents} documents · ${s.pages} pages · ${s.pages_checked} checked, ${s.pages_draft} draft</div></div>`;
  };
  const top = lb.slice(0, 5).map((r) => `<tr><td><a href="#/system/${esc(r.system)}">${esc(r.card.name || r.system)}</a></td>
    <td class="num">${pct(r.open?.scores.overall)}</td><td class="num">${pct(r.closed?.scores.overall)}</td></tr>`).join("");
  $app.innerHTML = `
    <h1>PW2 extraction benchmark</h1>
    <p class="lead">How well do local, open-weight systems pull text, tables, formulas and measurement records out of BAM technical documents? Public certificates form the open track. Internal reports form the closed track, which never leaves BAM.</p>
    <div class="tiles">${tile("open")}${tile("closed")}
      <div class="tile"><div class="k">Systems</div><div class="v">${ov.systems}</div><div class="s">${ov.leaderboard_rows} with results</div></div>
      ${agreeTile(ov.agreement)}
      <div class="tile"><div class="k">Release</div><div class="v">Nov 30</div><div class="s">v0.1, annotated pages frozen before the final runs</div></div>
    </div>
    <h2>Leaderboard, top systems</h2>
    ${lb.length ? `<div class="scroll"><table class="grid"><tr><th>System</th><th class="num">Open overall</th><th class="num">Closed overall</th></tr>${top}</table></div>
      <p class="small"><a href="#/leaderboard">Full leaderboard</a></p>` : `<p class="muted">No results yet. ${STATIC ? "Results appear here once summaries are committed to the repository." : 'Start one under <a href="#/runs">Runs</a>.'}</p>`}
    <div class="note small">All scores so far use <b>draft</b> labels written by one annotator. They show that the pipeline works; they are not yet benchmark results.</div>
    ${STATIC ? `<div class="note small">This is a read-only copy built ${esc(STATIC.built.replace("T", " ").slice(0, 16))} UTC${STATIC.commit ? ` from commit <code>${esc(STATIC.commit)}</code>` : ""}. It shows the open track, and closed-track scores only where at least 20 pages back them. Annotation, page comparison and model runs happen in the dashboard on the BAM cluster.</div>` : ""}`;
}

// ---------- Downloads ----------
const todayIso = () => new Date().toISOString().slice(0, 10);
function downloadBlob(fileName, blob) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
function downloadText(fileName, mime, text) { downloadBlob(fileName, new Blob([text], { type: mime })); }
// The charts are styled by CSS classes and variables, which a standalone image does not have. So copy the
// computed paint onto every element of a clone, put the panel colour behind it and draw it at twice the size.
function downloadSvgPng(svg, fileName) {
  const props = ["fill", "stroke", "stroke-width", "stroke-dasharray", "font-size", "font-family", "font-weight", "opacity"];
  const clone = svg.cloneNode(true);
  const src = [svg, ...svg.querySelectorAll("*")], dst = [clone, ...clone.querySelectorAll("*")];
  src.forEach((el, i) => {
    const cs = getComputedStyle(el);
    dst[i].setAttribute("style", props.map((p) => `${p}:${cs.getPropertyValue(p)}`).join(";"));
  });
  clone.querySelectorAll("title").forEach((t) => t.remove());
  const vb = svg.viewBox.baseVal, w = vb.width, h = vb.height, ns = "http://www.w3.org/2000/svg";
  clone.setAttribute("xmlns", ns);
  clone.setAttribute("width", w);
  clone.setAttribute("height", h);
  const bg = document.createElementNS(ns, "rect");
  bg.setAttribute("width", w);
  bg.setAttribute("height", h);
  bg.setAttribute("fill", getComputedStyle(document.documentElement).getPropertyValue("--panel").trim() || "#fff");
  clone.insertBefore(bg, clone.firstChild);
  const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(clone));
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement("canvas");
      c.width = w * 2;
      c.height = h * 2;
      const g = c.getContext("2d");
      g.scale(2, 2);
      g.drawImage(img, 0, 0, w, h);
      c.toBlob((b) => (b ? (downloadBlob(fileName, b), resolve()) : reject(new Error("Could not make the image"))), "image/png");
    };
    img.onerror = () => reject(new Error("Could not draw the chart"));
    img.src = url;
  });
}
const csvCell = (x) => {
  const t = x === null || x === undefined ? "" : String(x);
  return /[",\r\n]/.test(t) ? `"${t.replace(/"/g, '""')}"` : t;
};

// ---------- Leaderboard ----------
let lbTrack = store.get("lbTrack", "open");
// Every choice on the leaderboard is remembered.
const lbS = {
  sort: store.get("lb_sort", "overall"), view: store.get("lb_view", "fair"), cols: store.get("lb_cols", "all"),
  lic: store.get("lb_lic", "any"), pub: store.get("lb_pub", "any"), size: store.get("lb_size", "any"), type: store.get("lb_type", "any"),
  fit: store.get("lb_fit", "0") === "1", help: store.get("lb_help", "0") === "1",
};
const lbSet = (k, v) => { lbS[k] = v; store.set("lb_" + k, typeof v === "boolean" ? (v ? "1" : "0") : v); };
const LB_PRESETS = [
  ["all", "All", null],
  ["accuracy", "Accuracy", ["overall", "e1_text", "e2_table_teds", "e3_formula"]],
  ["tables", "Tables and numbers", ["overall", "e2_table_teds", "e2_table_teds_struct", "numbers_recall", "e5_record_f1"]],
  ["cost", "Cost", ["overall", "seconds_per_page", "eur_per_1000_pages", "output_tokens_per_page"]],
];
const LB_LANG = { de: "German", en: "English", "en+de": "bilingual" };
const lowIsGood = (k) => COSTS.some(([c]) => c === k);
// The scores of one summary in one view, or null when the view holds no pages. The fair view is the summary
// without the pages the system drafted itself, or all pages when it drafted none (or the run is old).
function lbPick(s, view) {
  let v;
  if (view === "all" || view === "fair") v = (view === "fair" && s.excluding_own_drafts) || { ...s.scores, pages: s.counts.pages, ci95: s.ci95 };
  else v = (view.startsWith("kind:") ? s.by_kind : s.by_lang)?.[view.slice(5)];
  if (!v || !v.pages) return null;
  // E5 is scored per document, so it has no per-kind or per-language value.
  const whole = view === "all" || view === "fair";
  return { pages: v.pages, scores: { ...v, e5_record_f1: whole ? s.scores.e5_record_f1 ?? null : null }, ci95: v.ci95 || null };
}
const ownDrafts = (s) => s.counts.own_draft_pages ?? (s.excluding_own_drafts ? s.counts.pages - s.excluding_own_drafts.pages : 0);
// "12B", "0.9B", "258M", "about 1B", "4B effective (8B with embeddings)": the first number. Null when there is none.
function paramsB(p) {
  const m = String(p ?? "").match(/(\d+(?:\.\d+)?)\s*([BM])(?![A-Za-z])/i);
  return m ? parseFloat(m[1]) / (m[2].toUpperCase() === "M" ? 1000 : 1) : null;
}
const isPermissive = (lic) => /^(apache|mit|bsd)/i.test(String(lic ?? "").trim());
function monthIndex(rel) { // "2026-03" or "2026-03-19" -> months since year 0; "2026" counts as January
  const m = String(rel ?? "").match(/^(\d{4})(?:-(\d{2}))?/);
  return m ? +m[1] * 12 + (m[2] ? +m[2] - 1 : 0) : null;
}

async function leaderboard() {
  const [rows, mod, ov] = await Promise.all([api("leaderboard"), api("models"), api("overview").catch(() => null)]);
  const rel = Object.fromEntries(mod.systems.map((s) => [s.id, s.released]));
  const val = (it, k) => (k in (it.p?.scores || {}) ? it.p.scores[k] : it.s.cost?.[k]) ?? null;
  // 95% bootstrap interval over pages, shown under a score when the run recorded one.
  const ci = (p, k) => (p?.ci95?.[k] ? `<div class="ci" title="95% interval: where this score would likely fall with a different sample of pages">${pct(p.ci95[k][0])}–${pct(p.ci95[k][1])}</div>` : "");
  const metricLabel = (k) => [...METRICS, ...COSTS].find(([c]) => c === k)?.[1] ?? k;
  const draw = () => {
    const focus = document.activeElement?.dataset?.ctl;
    const track = lbTrack;
    const all = rows.filter((r) => r[track]);
    // Choices that depend on the data: page kinds, languages, publishers. A stale remembered choice falls back.
    const kinds = [...new Set(all.flatMap((r) => Object.keys(r[track].by_kind || {})))].sort();
    const langs = [...new Set(all.flatMap((r) => Object.keys(r[track].by_lang || {})))].sort();
    const pubs = [...new Set(all.map((r) => r.card.publisher).filter(Boolean))].sort();
    const viewOpts = [["fair", "Fair: without a system's own drafts"], ["all", "All pages"],
      ...kinds.map((k) => ["kind:" + k, `Only ${k} pages`]), ...langs.map((l) => ["lang:" + l, `Only ${LB_LANG[l] || l} pages`])];
    if (!viewOpts.some(([v]) => v === lbS.view)) lbSet("view", "fair");
    if (lbS.pub !== "any" && !pubs.includes(lbS.pub)) lbSet("pub", "any");
    const preset = LB_PRESETS.find(([k]) => k === lbS.cols) || LB_PRESETS[0];
    const shownCols = preset[2];
    const show = (k) => !shownCols || shownCols.includes(k);
    if (!show(lbS.sort)) lbSet("sort", "overall");
    const view = lbS.view;

    const items = all.map((r) => ({ r, s: r[track], p: lbPick(r[track], view) })).filter(({ r, s }) => {
      const c = r.card, b = paramsB(c.params);
      if (lbS.lic !== "any" && isPermissive(c.license) !== (lbS.lic === "permissive")) return false;
      if (lbS.pub !== "any" && c.publisher !== lbS.pub) return false;
      if (lbS.size === "none" ? b !== null : lbS.size !== "any" && (b === null || (lbS.size === "s" ? b > 4 : lbS.size === "m" ? b <= 4 || b > 10 : b <= 10))) return false;
      if (lbS.type !== "any" && (c.kind === "vllm") !== (lbS.type === "vision")) return false;
      if (lbS.fit && !(s.cost?.gpu_share <= 0.25)) return false;
      return true;
    });
    const up = lowIsGood(lbS.sort);
    items.sort((a, b) => {
      const x = val(a, lbS.sort), y = val(b, lbS.sort);
      if (x === null || y === null) return (x === null) - (y === null);
      return up ? x - y : y - x;
    });
    const best = {};
    for (const [k] of METRICS) best[k] = Math.max(...items.map((it) => it.p?.scores[k] ?? -1));
    for (const [k] of COSTS) {
      const xs = items.map((it) => it.s.cost?.[k]).filter((x) => x !== null && x !== undefined && x > 0);
      best[k] = xs.length ? Math.min(...xs) : null;
    }
    const arrow = (k) => (lbS.sort === k ? (lowIsGood(k) ? " ↑" : " ↓") : "");
    const head = METRICS.filter(([k]) => show(k)).map(([k, label, tip]) => `<th class="num sort" tabindex="0" data-k="${k}" title="${esc(tip)}">${label}${arrow(k)}</th>`).join("")
      + COSTS.filter(([k]) => show(k)).map(([k, label, tip]) => `<th class="num sort cost" tabindex="0" data-k="${k}" title="${esc(tip)}">${label}${arrow(k)}</th>`).join("");
    const body = items.map(({ r, s, p }, i) => {
      const cells = METRICS.filter(([k]) => show(k)).map(([k]) => {
        const v = p?.scores[k] ?? null;
        return `<td class="num ${items.length > 1 && v !== null && v === best[k] ? "best" : ""}">${pct(v)}${ci(p, k)}</td>`;
      }).join("");
      const costs = COSTS.filter(([k]) => show(k)).map(([k, , , fmt]) => {
        const x = s.cost?.[k];
        const cut = k === "output_tokens_per_page" && s.cost?.truncated_pages ? ` <span class="small muted" title="Replies cut off at max_tokens">${s.cost.truncated_pages} cut</span>` : "";
        return `<td class="num cost ${items.length > 1 && x && x === best[k] ? "best" : ""}">${x === null || x === undefined ? "—" : fmt(x)}${cut}</td>`;
      }).join("");
      const n = ownDrafts(s);
      const dagger = n > 0 ? ` <span class="dagger" title="Labels for ${n} of ${s.counts.pages} pages started from this system's own draft. The fair view leaves those pages out for this system.">†</span>` : "";
      const pages = p ? (p.pages < s.counts.pages ? `${p.pages} of ${s.counts.pages}` : p.pages) : "—";
      return `<tr class="click" data-sys="${esc(r.system)}"><td class="num muted">${i + 1}</td>
        <td><b>${esc(r.card.name || r.system)}</b>${dagger}<div class="small muted">${esc(r.card.params || "")} · ${esc(r.card.license || "")}${r.card.slice ? " · " + esc(r.card.slice) : ""}</div></td>
        ${cells}${costs}<td class="num">${pages}${p && p.pages < 5 ? ' <span class="pill draft" title="This score rests on too few pages to mean much.">few pages</span>' : ""}${s.publishable === false ? ' <span class="pill draft" title="Fewer than 20 pages: internal only">internal</span>' : ""}${s.counts.gold_pages_not_predicted ? ` <span class="pill no" title="${s.counts.gold_pages_not_predicted} annotated pages were added after this run. Rerun the system to cover them.">stale</span>` : ""}${s.scorer_current === false ? ' <span class="pill draft" title="Scored with an older version of the metrics. Run bambench rescore to update it; no model run is needed.">old scoring</span>' : ""}</td><td class="small muted">${esc(s.finished.slice(0, 10))}</td></tr>`;
    }).join("");
    const price = all.find((r) => r[track].cost)?.[track].cost.eur_per_hour;
    const opts = (xs, cur) => xs.map(([v, l]) => `<option value="${esc(v)}" ${v === cur ? "selected" : ""}>${esc(l)}</option>`).join("");
    const sel = (ctl, label, xs, cur) => `<label class="ctl">${label}<select data-ctl="${ctl}">${opts(xs, cur)}</select></label>`;
    const filtering = lbS.lic !== "any" || lbS.pub !== "any" || lbS.size !== "any" || lbS.type !== "any" || lbS.fit;
    const toolbar = `<div class="lbbar">
      ${sel("view", "Pages", viewOpts, view)}
      ${sel("cols", "Columns", LB_PRESETS.map(([k, l]) => [k, l]), preset[0])}
      ${sel("lic", "Licence", [["any", "Any"], ["permissive", "Permissive (Apache, MIT, BSD)"], ["other", "Other"]], lbS.lic)}
      ${sel("pub", "Publisher", [["any", "Any"], ...pubs.map((p) => [p, p])], lbS.pub)}
      ${sel("size", "Size", [["any", "Any"], ["s", "Up to 4B"], ["m", "4B to 10B"], ["l", "Over 10B"], ["none", "No model weights"]], lbS.size)}
      ${sel("type", "Type", [["any", "Any"], ["vision", "Vision model"], ["pipeline", "Pipeline or baseline"]], lbS.type)}
      <label class="chk"><input type="checkbox" data-ctl="fit" ${lbS.fit ? "checked" : ""}> Fits a 20 GB slice</label>
      ${filtering ? '<button class="btn" data-ctl="reset">Reset</button>' : ""}
      <span class="grow"></span>
      ${items.length ? '<button class="btn" data-ctl="csv" title="All columns, the rows as shown">Download CSV</button>' : ""}
    </div>`;
    const help = `<details class="help" id="lb-help" ${lbS.help ? "open" : ""}><summary>How to read this table</summary><dl>
      <dt>Scores</dt><dd>Scores are percentages from 0 to 100, and higher is better. Overall is the mean of E1 Text, E2 Tables and E3 Formulas. Numbers and E5 Records are shown beside it and are not part of Overall.</dd>
      <dt>The range under a score</dt><dd>${all.some((r) => r[track].ci95) ? "The small range is a 95% interval, from resampling the annotated pages 1,000 times. When two systems' ranges overlap, the benchmark cannot yet tell them apart; more annotated pages narrow the ranges. " : ""}${all.some((r) => !r[track].ci95) ? "Runs made before Nov 10 show no interval. Run <code>python3 -m bambench rescore --track " + track + "</code> to add one without rerunning any model." : ""}</dd>
      <dt>Fair view and the dagger †</dt><dd>A system tends to score better on a page whose label started as its own draft. The fair view leaves those pages out for that system, so each system may be scored on a different number of pages. A dagger † marks a system that drafted labels on this track.</dd>
      <dt>Other views</dt><dd>All pages counts every scored page. A page-kind or language view scores only the pages of that kind or language. E5 Records is scored per document, so it shows only in the fair and all-pages views. Cost is the same in every view.</dd>
      <dt>Bold</dt><dd>Bold marks the best value in a column among the rows shown, so a filter can change it.</dd>
      <dt>Pills</dt><dd><span class="pill draft">internal</span> fewer than 20 pages, for internal use only. <span class="pill no">stale</span> scored on fewer pages than are annotated now; it needs a rerun. <span class="pill draft">old scoring</span> scored with an older version of the metrics; <code>bambench rescore</code> updates it with no model run. <span class="pill draft">few pages</span> the view holds fewer than 5 pages.</dd>
      <dt>Cost</dt><dd>Cost is an estimate: the share of one A100 80 GB the system's slice takes (20 GB is a quarter, 40 GB a half, CPU is free) × run time × €${price ?? "?"} per A100 hour. Set BAMBENCH_A100_EUR_PER_HOUR to change the price. Time is measured with the model already loaded, so server start-up is not counted.${all.some((r) => r[track].counts.gold_pages_not_predicted) ? " A row marked stale was scored on fewer pages than are annotated now." : ""}</dd>
    </dl></details>`;
    const dots = items.map(({ r, p, s }) => ({ name: r.card.name || r.system, sys: r.system, y: p?.scores.overall, x: s.cost?.seconds_per_page }));
    const speed = speedChart(dots);
    const dated = items.filter((it) => it.p?.scores.overall != null && monthIndex(rel[it.r.system] ?? it.r.card.released) !== null);
    const undated = items.filter((it) => it.p?.scores.overall != null).length - dated.length;
    const prog = progressChart(dated.map((it) => ({ name: it.r.card.name || it.r.system, sys: it.r.system, y: it.p.scores.overall, rel: rel[it.r.system] ?? it.r.card.released, d: monthIndex(rel[it.r.system] ?? it.r.card.released) })));
    const chartHead = (title, id, html) => `<div class="charthead"><h2>${title}</h2>${html.includes("<svg") ? `<button class="btn small" data-png="${id}" title="Save the chart as an image">PNG</button>` : ""}</div>`;
    $app.innerHTML = `<h1>Leaderboard</h1>
      <p class="lead">Scores are percentages, higher is better. Time and cost are per page, lower is better. Click a column to sort and a row for details. Every row was produced by a local run with a pinned system card.</p>
      ${help}
      <div class="tabs"><button data-t="open" class="${track === "open" ? "on" : ""}">Open track</button><button data-t="closed" class="${track === "closed" ? "on" : ""}">Closed track</button></div>
      ${track === "closed" ? `<div class="note closed small">Closed-track numbers are aggregates over confidential reports. Only publish a number when it is backed by at least 20 pages.</div>` : ""}
      ${agreeLine(ov?.agreement, track)}
      ${all.length ? `${toolbar}
        <p class="small muted">Showing ${items.length} of ${all.length} ${all.length === 1 ? "system" : "systems"} with a result on this track, sorted by ${esc(metricLabel(lbS.sort))}. ${mod.systems.length} systems are in the benchmark; the others are listed with their status under <a href="#/models">Models</a>.</p>
        ${items.length ? `<div class="scroll"><table class="grid"><tr><th class="num">#</th><th>System</th>${head}<th class="num">Pages</th><th>Run</th></tr>${body}</table></div>` : `<p class="muted">No system matches these filters.</p>`}
        ${chartHead("Accuracy against speed", "speed", speed)}${speed}
        ${chartHead("Progress over time", "progress", prog)}${prog}
        ${undated && prog.includes("<svg") ? `<p class="small muted">${undated} system${undated === 1 ? " has" : "s have"} no release date and ${undated === 1 ? "is" : "are"} left out.</p>` : ""}`
        : `<p class="muted">No ${track}-track results yet.</p>`}`;
    $app.querySelectorAll("[data-t]").forEach((b) => (b.onclick = () => { lbTrack = b.dataset.t; store.set("lbTrack", lbTrack); draw(); }));
    $app.querySelectorAll("th[data-k]").forEach((th) => {
      th.onclick = () => { lbSet("sort", th.dataset.k); draw(); };
      th.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); th.click(); } };
    });
    $app.querySelectorAll("tr[data-sys], g[data-sys]").forEach((el) => (el.onclick = () => (location.hash = "#/system/" + el.dataset.sys)));
    $app.querySelectorAll("select[data-ctl]").forEach((el) => (el.onchange = () => { lbSet(el.dataset.ctl, el.value); draw(); }));
    const fit = $app.querySelector('[data-ctl="fit"]');
    if (fit) fit.onchange = () => { lbSet("fit", fit.checked); draw(); };
    const reset = $app.querySelector('[data-ctl="reset"]');
    if (reset) reset.onclick = () => { for (const k of ["lic", "pub", "size", "type"]) lbSet(k, "any"); lbSet("fit", false); draw(); };
    const det = document.getElementById("lb-help");
    if (det) det.ontoggle = () => lbSet("help", det.open);
    const csv = $app.querySelector('[data-ctl="csv"]');
    if (csv) csv.onclick = () => exportCsv(items, track, view);
    $app.querySelectorAll("[data-png]").forEach((b) => (b.onclick = () => {
      const svg = $app.querySelector(`svg[data-chart="${b.dataset.png}"]`);
      if (svg) downloadSvgPng(svg, `bambench-${b.dataset.png}-${track}-${todayIso()}.png`).catch((e) => toast(e.message));
    }));
    if (focus) $app.querySelector(`[data-ctl="${focus}"]`)?.focus();
  };
  draw();
}

// The rows as shown (track, view, filters, order), with every column whatever the column preset.
function exportCsv(items, track, view) {
  const keys = ["overall", "e1_text", "e2_table_teds", "e2_table_teds_struct", "e3_formula", "numbers_recall"];
  const f4 = (x) => (x === null || x === undefined ? "" : x.toFixed(4));
  const head = ["rank", "system", "name", "publisher", "licence", "params", "slice", "track", "view", "pages", "pages_in_run", "own_draft_pages",
    ...keys.flatMap((k) => [k, k + "_lo", k + "_hi"]), "e5_record_f1", "seconds_per_page", "eur_per_1000_pages", "output_tokens_per_page", "publishable", "scorer_current", "finished"];
  const lines = [head.join(",")];
  items.forEach(({ r, s, p }, i) => {
    const c = r.card, iv = p?.ci95 || {};
    lines.push([i + 1, r.system, c.name || r.system, c.publisher, c.license, c.params, c.slice, track, view, p ? p.pages : 0, s.counts.pages, s.counts.own_draft_pages,
      ...keys.flatMap((k) => [f4(p?.scores[k]), f4(iv[k]?.[0]), f4(iv[k]?.[1])]), f4(p?.scores.e5_record_f1),
      s.cost?.seconds_per_page, s.cost?.eur_per_1000_pages, s.cost?.output_tokens_per_page,
      s.publishable ?? true, s.scorer_current ?? "", s.finished].map(csvCell).join(","));
  });
  const internal = track === "closed" && items.some(({ s }) => s.publishable === false);
  const slug = view.replace(/[^a-z0-9]+/gi, "-");
  downloadText(`bambench-${track}-${slug}-${todayIso()}${internal ? "-internal" : ""}.csv`, "text/csv;charset=utf-8", lines.join("\n") + "\n");
}

// Place each label right, left, above or below its dot, avoiding other dots and labels already placed.
// `boxes` holds every dot and grows with each label. Returns one [x, y, anchor] per entry of `dots`.
function placeLabels(dots, boxes, W, L) {
  const hit = (r) => r.x1 < L || r.x2 > W - 2 || boxes.some((b) => r.x1 < b.x2 && b.x1 < r.x2 && r.y1 < b.y2 && b.y1 < r.y2);
  return dots.map(({ cx, cy, label }) => {
    const w = label.length * 6.3;
    const spots = [[cx + 8, cy + 4, "start"], [cx - 8, cy + 4, "end"], [cx, cy - 10, "middle"], [cx, cy + 18, "middle"]];
    let pick = spots[0], box;
    for (let dy = 0; dy <= 39; dy += 13) {
      const found = spots.find(([x, y, a]) => {
        const x1 = a === "start" ? x : a === "end" ? x - w : x - w / 2;
        box = { x1, x2: x1 + w, y1: y + dy - 11, y2: y + dy + 2 };
        return !hit(box);
      });
      if (found) { pick = [found[0], found[1] + dy, found[2]]; break; }
    }
    const x1 = pick[2] === "start" ? pick[0] : pick[2] === "end" ? pick[0] - w : pick[0] - w / 2;
    boxes.push({ x1, x2: x1 + w, y1: pick[1] - 11, y2: pick[1] + 2 });
    return pick;
  });
}
const shortName = (n) => n.replace(/\s*\(.*\)$/, "");

// Overall score (up) against seconds per page (left is faster), log scale on time. Top left is best.
function speedChart(points) {
  const pts = points.filter((p) => p.y !== null && p.y !== undefined && p.x > 0);
  if (pts.length < 2) return `<p class="small muted">Needs two systems with timed runs.</p>`;
  const W = 720, H = 360, L = 52, R = 24, T = 16, B = 44;
  const lo = Math.log10(Math.min(...pts.map((p) => p.x)) / 1.3), hi = Math.log10(Math.max(...pts.map((p) => p.x)) * 1.3);
  const ymax = Math.min(1, Math.ceil(Math.max(...pts.map((p) => p.y)) * 10 + 0.5) / 10);
  const X = (x) => L + ((Math.log10(x) - lo) / (hi - lo)) * (W - L - R);
  const Y = (y) => T + (1 - y / ymax) * (H - T - B);
  const xt = [1, 2, 5, 10, 20, 50, 100, 200, 500].filter((v) => Math.log10(v) >= lo && Math.log10(v) <= hi);
  const yt = []; for (let v = 0; v <= ymax + 1e-9; v += 0.1) yt.push(+v.toFixed(1));
  const grid = yt.map((v) => `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" class="gridline"/><text x="${L - 8}" y="${Y(v) + 4}" text-anchor="end">${Math.round(v * 100)}</text>`).join("")
    + xt.map((v) => `<text x="${X(v)}" y="${H - B + 18}" text-anchor="middle">${v}</text>`).join("");
  const order = [...pts].sort((a, b) => b.y - a.y);
  const boxes = pts.map((p) => ({ x1: X(p.x) - 6, x2: X(p.x) + 6, y1: Y(p.y) - 6, y2: Y(p.y) + 6 }));
  const picks = placeLabels(order.map((p) => ({ cx: X(p.x), cy: Y(p.y), label: shortName(p.name) })), boxes, W, L);
  const dots = order.map((p, i) => `<g class="pt" data-sys="${esc(p.sys)}"><title>${esc(p.name)}: ${pct(p.y)} overall, ${p.x.toFixed(1)} s per page</title>
    <circle cx="${X(p.x)}" cy="${Y(p.y)}" r="5"/><text x="${picks[i][0]}" y="${picks[i][1]}" text-anchor="${picks[i][2]}">${esc(shortName(p.name))}</text></g>`).join("");
  return `<div class="scroll"><svg class="chart" data-chart="speed" viewBox="0 0 ${W} ${H}" role="img" aria-label="Overall score against seconds per page">
    ${grid}<line x1="${L}" x2="${W - R}" y1="${Y(0)}" y2="${Y(0)}" class="axis"/>
    <text x="${(L + W - R) / 2}" y="${H - 6}" text-anchor="middle" class="label">Seconds per page (log scale, faster to the left)</text>
    <text x="14" y="${(T + H - B) / 2}" text-anchor="middle" class="label" transform="rotate(-90 14 ${(T + H - B) / 2})">Overall</text>
    ${dots}</svg></div>`;
}

// Overall score (up) against release month (across), with a step line of the best score so far.
// Only a dot that sets a new best is labelled.
function progressChart(points) {
  if (points.length < 2) return `<p class="small muted">Needs two systems with a release date.</p>`;
  const W = 720, H = 360, L = 52, R = 24, T = 16, B = 44;
  const lo = Math.min(...points.map((p) => p.d)) - 2, hi = Math.max(...points.map((p) => p.d)) + 2;
  const ymax = Math.min(1, Math.ceil(Math.max(...points.map((p) => p.y)) * 10 + 0.5) / 10);
  const X = (d) => L + ((d - lo) / (hi - lo)) * (W - L - R);
  const Y = (y) => T + (1 - y / ymax) * (H - T - B);
  const yt = []; for (let v = 0; v <= ymax + 1e-9; v += 0.1) yt.push(+v.toFixed(1));
  const ticks = [];
  if (hi - lo >= 14) for (let y = Math.ceil(lo / 12); y * 12 <= hi; y++) ticks.push([y * 12, String(y)]);
  else for (let v = Math.ceil(lo / 3) * 3; v <= hi; v += 3) ticks.push([v, `${Math.floor(v / 12)}-${String((v % 12) + 1).padStart(2, "0")}`]);
  const grid = yt.map((v) => `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" class="gridline"/><text x="${L - 8}" y="${Y(v) + 4}" text-anchor="end">${Math.round(v * 100)}</text>`).join("")
    + ticks.map(([v, l]) => `<line x1="${X(v)}" x2="${X(v)}" y1="${Y(0)}" y2="${Y(0) + 4}" class="axis"/><text x="${X(v)}" y="${H - B + 18}" text-anchor="middle">${l}</text>`).join("");
  const byDate = [...points].sort((a, b) => a.d - b.d || b.y - a.y);
  let top = -1;
  const records = byDate.filter((p) => (p.y > top ? ((top = p.y), true) : false));
  const path = records.map((p, i) => (i ? `H${X(p.d)} V${Y(p.y)}` : `M${X(p.d)} ${Y(p.y)}`)).join(" ") + ` H${W - R}`;
  const boxes = points.map((p) => ({ x1: X(p.d) - 6, x2: X(p.d) + 6, y1: Y(p.y) - 6, y2: Y(p.y) + 6 }));
  const picks = placeLabels(records.map((p) => ({ cx: X(p.d), cy: Y(p.y), label: shortName(p.name) })), boxes, W, L);
  const dot = (p, label) => `<g class="pt" data-sys="${esc(p.sys)}"><title>${esc(p.name)}: released ${esc(String(p.rel).slice(0, 7))}, ${pct(p.y)} overall</title>
    <circle cx="${X(p.d)}" cy="${Y(p.y)}" r="5"/>${label ? `<text x="${label[0]}" y="${label[1]}" text-anchor="${label[2]}">${esc(shortName(p.name))}</text>` : ""}</g>`;
  const dots = byDate.filter((p) => !records.includes(p)).map((p) => dot(p)).join("") + records.map((p, i) => dot(p, picks[i])).join("");
  return `<div class="scroll"><svg class="chart" data-chart="progress" viewBox="0 0 ${W} ${H}" role="img" aria-label="Overall score against release month">
    ${grid}<line x1="${L}" x2="${W - R}" y1="${Y(0)}" y2="${Y(0)}" class="axis"/><path class="step" d="${path}"/>
    <text x="${(L + W - R) / 2}" y="${H - 6}" text-anchor="middle" class="label">Release month of the model (line: best score so far)</text>
    <text x="14" y="${(T + H - B) / 2}" text-anchor="middle" class="label" transform="rotate(-90 14 ${(T + H - B) / 2})">Overall</text>
    ${dots}</svg></div>`;
}

// ---------- System detail ----------
const STATUS_PILL = { active: "ok", pending: "", failed: "failed", superseded: "superseded", withdrawn: "withdrawn" };
const statusPill = (s) => `<span class="pill ${STATUS_PILL[s] ?? ""}">${esc(s)}</span>`;
const CARD_LABEL = { kind: "Kind", model: "Model", weights_gb: "Weights (GB)", gpu: "GPU memory", serve: "Serve command", output: "Output format", notes: "Notes",
  handles: "Claimed to handle", env: "Environment variables", extra_body: "Extra request fields", records: "Extracts E5 records", revision: "Weights revision",
  max_tokens: "Max tokens", prompt: "Prompt", params: "Size", license: "Licence", slice: "GPU slice" };
// Keys the header already shows, and the fields the models endpoint adds on top of the card.
const CARD_SKIP = new Set(["id", "name", "publisher", "released", "license", "params", "slice", "source", "paper", "repo", "status", "status_note", "superseded_by",
  "available", "reason", "weights_downloaded", "results", "seconds_per_page", "failure"]);
function cardValue(k, v) {
  const yn = (x) => (x === true ? "yes" : x === false ? "no" : "unknown");
  if (v === null || v === undefined || v === "") return '<span class="muted">—</span>';
  if (k === "handles" && typeof v === "object") return esc(Object.entries(v).map(([c, x]) => `${c} ${yn(x)}`).join(", "));
  if (typeof v === "boolean") return yn(v);
  if (Array.isArray(v)) return esc(v.join(", "));
  if (typeof v === "object") {
    const flat = Object.values(v).every((x) => x === null || typeof x !== "object");
    return flat ? esc(Object.entries(v).map(([a, b]) => `${a}: ${typeof b === "boolean" ? yn(b) : b}`).join(", ")) : `<code>${esc(JSON.stringify(v))}</code>`;
  }
  if (typeof v === "string" && /^https?:\/\//.test(v)) return `<a href="${esc(v)}" target="_blank" rel="noopener">${esc(v)}</a>`;
  return ["serve", "model", "revision"].includes(k) ? `<code>${esc(v)}</code>` : esc(v);
}
async function systemDetail(id) {
  const [rows, m] = await Promise.all([api("leaderboard"), api("models")]);
  const r = rows.find((x) => x.system === id);
  const ms = m.systems.find((x) => x.id === id);
  if (!r && !ms) { $app.innerHTML = `<p class="small"><a href="#/leaderboard">← Leaderboard</a></p><p>No system called ${esc(id)}.</p>`; return; }
  const card = ms || r.card;
  const name = card.name || id;
  const nameOf = (sid) => m.systems.find((x) => x.id === sid)?.name || sid;
  const status = ms?.status || (r ? "active" : "pending");
  const tracks = ["open", "closed"].filter((t) => r?.[t]);
  const link = (label, u) => (typeof u === "string" && /^https?:\/\//.test(u) ? `<a href="${esc(u)}" target="_blank" rel="noopener">${label}</a>` : "");
  const fails = status === "failed" ? ["open", "closed"].filter((t) => ms?.failure?.[t]).map((t) =>
    `<div class="note small">The last ${t}-track run failed on ${esc(ms.failure[t].when.slice(0, 10))}: ${esc(ms.failure[t].error)}</div>`).join("") : "";
  const facts = [card.publisher && esc(card.publisher), card.released && "Released " + esc(card.released), card.params && "Size " + esc(card.params),
    card.license && `Licence ${esc(card.license)} <span class="muted">as stated by the publisher</span>`, card.slice && "Slice " + esc(card.slice)].filter(Boolean);
  const links = [link("Model card", card.source), link("Paper", card.paper), link("Code", card.repo)].filter(Boolean);
  const header = `<p class="small"><a href="#/leaderboard">← Leaderboard</a></p><h1>${esc(name)}</h1>
    <p>${statusPill(status)} ${card.status_note ? `<span class="muted">${esc(card.status_note)}</span>` : ""}
      ${status === "superseded" && card.superseded_by ? ` Replaced by <a href="#/system/${esc(card.superseded_by)}">${esc(nameOf(card.superseded_by))}</a>.` : ""}</p>
    ${fails}
    <p class="facts small muted">${facts.join(" · ")}</p>${links.length ? `<p class="small links">${links.join(" · ")}</p>` : ""}`;

  let docs = "";
  try {
    if (STATIC || !r?.open) throw new Error("per-document scores live with the run folders, which a hosted copy does not carry");
    const run = await api(`runs/open/${encodeURIComponent(id)}/latest`);
    docs = run.documents.map((d) => {
      const pages = Object.values(d.pages);
      const text = pages.length ? pages.reduce((a, p) => a + p.text_score, 0) / pages.length : null;
      const tabs = pages.flatMap((p) => p.tables.map((t) => t.teds));
      const teds = tabs.length ? tabs.reduce((a, b) => a + b, 0) / tabs.length : null;
      return `<tr><td>${esc(d.document_id)}</td><td class="num">${pages.length}</td><td class="num">${pct(text)}</td><td class="num">${pct(teds)}</td>
        <td class="num">${d.records ? pct(d.records.record_f1) : "—"}</td></tr>`;
    }).join("");
  } catch { /* no open run */ }

  const kinds = (t) => {
    const k = r[t].by_kind;
    if (!k || !Object.keys(k).length) return "";
    const line = ([n, v]) => `<tr><td>${esc(n)}</td><td class="num">${v.pages}</td><td class="num">${pct(v.overall)}${ci(v, "overall")}</td>
      <td class="num">${pct(v.e1_text)}</td><td class="num">${pct(v.e2_table_teds)}</td><td class="num">${pct(v.e3_formula)}</td><td class="num">${pct(v.numbers_recall)}</td></tr>`;
    const ci = (v, key) => (v.ci95?.[key] ? `<div class="ci">${pct(v.ci95[key][0])}–${pct(v.ci95[key][1])}</div>` : "");
    const langs = Object.entries(r[t].by_lang || {});
    const th = (a) => `<tr><th>${a}</th><th class="num">Pages</th><th class="num">Overall</th><th class="num">E1</th><th class="num">E2</th><th class="num">E3</th><th class="num">Numbers</th></tr>`;
    return `<h3>By page kind, ${t} track</h3><div class="scroll"><table class="grid">${th("Kind")}${Object.entries(k).map(line).join("")}</table></div>
      ${langs.length > 1 ? `<h3>By language, ${t} track</h3><div class="scroll"><table class="grid">${th("Language")}${langs.map(line).join("")}</table></div>` : ""}`;
  };
  const rankOf = (t, k, v, get) => {
    const peers = rows.filter((x) => x[t]);
    if (v === null || v === undefined) return "—";
    return `#${1 + peers.filter((x) => (get(x[t]) ?? -1) > v).length} of ${peers.length}`;
  };
  const section = (t) => {
    const s = r[t];
    const tiles = METRICS.map(([k, l]) => `<div class="tile"><div class="k">${l}</div><div class="v">${pct(s.scores[k])}</div>
      ${s.ci95?.[k] ? `<div class="s">95% interval ${pct(s.ci95[k][0])} to ${pct(s.ci95[k][1])}</div>` : ""}
      <div class="s rank" title="Rank among the systems with a result on this track, all pages">${rankOf(t, k, s.scores[k], (x) => x.scores[k])}</div></div>`).join("");
    const n = ownDrafts(s), ex = s.excluding_own_drafts;
    let dag = "";
    if (n > 0) {
      const fair = (x) => lbPick(x, "fair")?.scores.overall;
      dag = ex && ex.pages
        ? `† This system drafted the labels of ${n} of ${s.counts.pages} pages. Without them it scores ${pct(ex.overall)} overall on ${ex.pages} pages${ex.ci95?.overall ? ` (95% interval ${pct(ex.ci95.overall[0])} to ${pct(ex.ci95.overall[1])})` : ""}, which is rank ${rankOf(t, "overall", fair(s), (x) => fair(x))} in the fair view the leaderboard uses.`
        : `† This system drafted the labels of ${n} of ${s.counts.pages} pages, so no page is left for a fair score.`;
    }
    const others = rows.filter((x) => x[t] && x.system !== id).sort((a, b) => (a.card.name || a.system).localeCompare(b.card.name || b.system));
    const cmp = others.length && !(STATIC && t === "closed")
      ? `<label class="ctl">Compare with…<select data-cmp="${t}"><option value="">Choose a system</option>${others.map((x) => `<option value="${esc(x.system)}">${esc(x.card.name || x.system)}</option>`).join("")}</select></label>` : "";
    return `<h2>${t === "open" ? "Open" : "Closed"} track ${trackPill(t)}</h2><div class="tiles">${tiles}</div>
      ${dag ? `<div class="note small">${dag}</div>` : ""}${cmp ? `<p>${cmp}</p>` : ""}${kinds(t)}`;
  };

  // How the system is run: the job script starts the model server on the GPU node.
  const gres = card.slice === "20 GB" ? "2g.20gb" : card.slice === "40 GB" ? "4g.40gb" : "1";
  const cmd = card.serve
    ? `sbatch --gres=gpu:${gres}:1 slurm/serve_and_run.sbatch ${id} closed\n# The job starts this model server on the GPU node:\n${card.serve}\n# then runs the system against it:\npython3 -m bambench run ${id} --track closed`
    : `python3 -m bambench run ${id} --track closed`;
  const runIt = `<h2>Run it</h2>
    <p class="small muted">${card.serve ? "Submit the first line from the repository folder. The job starts the model server on the GPU node, runs the system and stops the server. The lines below it show what the job does." : "This system needs no model server. Run it from the repository folder."}</p>
    <div class="cmdbox"><pre class="cmd"><code>${esc(cmd)}</code></pre>${navigator.clipboard ? '<button class="btn small" id="copy-cmd">Copy</button>' : ""}</div>`;

  const nr = '<span class="muted">not recorded</span>';
  const record = (t) => {
    const s = r[t], e = s.environment || {};
    const kv = (o) => (o && Object.keys(o).length ? esc(Object.entries(o).map(([a, b]) => `${a} ${b}`).join(", ")) : nr);
    const rev = e.weights_revision || card.revision;
    const c = s.cost;
    const line = [
      ["Run id", `<code>${esc(s.run_id)}</code>`],
      ["Finished", esc(String(s.finished).replace("T", " ").slice(0, 16)) + " UTC"],
      ...(s.rescored ? [["Rescored", typeof s.rescored === "string" ? esc(s.rescored.replace("T", " ").slice(0, 16)) + " UTC" : "yes"]] : []),
      ["Scorer version", `${esc(s.scorer ?? "")}${s.scorer_current === false ? ' <span class="pill draft" title="Scored with an older version of the metrics. Run bambench rescore to update it; no model run is needed.">old scoring</span>' : ""}` || nr],
      ["GPU", e.gpu ? esc(e.gpu) : nr], ["Python", e.python ? esc(e.python) : nr], ["Packages", kv(e.packages)], ["Model server", kv(e.server)],
      ["Weights revision", rev ? `<code title="${esc(rev)}">${esc(rev.slice(0, 12))}</code>` : nr],
      ["Time", s.runtime_s != null ? `${esc(s.runtime_s)} s${c?.seconds_per_page != null ? ` (${esc(c.seconds_per_page)} s per page)` : ""}` : nr],
      ["Cost", c?.eur_per_1000_pages != null ? `about €${esc(c.eur_per_1000_pages)} per 1,000 pages` : nr],
      ["Tokens", c?.output_tokens_per_page != null ? `${esc(c.prompt_tokens_per_page)} in, ${esc(c.output_tokens_per_page)} out per page${c.truncated_pages ? `, ${c.truncated_pages} replies cut off` : ""}` : nr],
    ];
    return `<h3>${t} track ${trackPill(t)}</h3><div class="scroll"><table class="grid kv">${line.map(([a, b]) => `<tr><th>${a}</th><td>${b}</td></tr>`).join("")}</table></div>`;
  };
  const cardRows = Object.entries(r ? r.card : card).filter(([k]) => !CARD_SKIP.has(k))
    .map(([k, v]) => `<tr><th>${esc(CARD_LABEL[k] || k.charAt(0).toUpperCase() + k.slice(1).replace(/_/g, " "))}</th><td>${cardValue(k, v)}</td></tr>`).join("");

  $app.innerHTML = `${header}
    ${tracks.length ? tracks.map(section).join("") : `<div class="note small">No result on either track yet.</div>`}
    ${docs ? `<h2>Per document, open track</h2><div class="scroll"><table class="grid"><tr><th>Document</th><th class="num">Pages</th><th class="num">E1 Text</th><th class="num">E2 Tables</th><th class="num">E5 Records</th></tr>${docs}</table></div>` : ""}
    ${runIt}
    ${tracks.length ? `<h2>Run record</h2>${tracks.map(record).join("")}` : ""}
    <h2>System card</h2><div class="scroll"><table class="grid kv">${cardRows}</table></div>`;
  $app.querySelectorAll("select[data-cmp]").forEach((el) => (el.onchange = () => { if (el.value) location.hash = `#/versus/${el.dataset.cmp}/${encodeURIComponent(id)}/${encodeURIComponent(el.value)}`; }));
  const copy = document.getElementById("copy-cmd");
  if (copy) copy.onclick = () => navigator.clipboard.writeText(cmd).then(() => toast("Copied"), () => toast("Could not copy. Select the text instead."));
}

// ---------- Documents ----------
async function documents() {
  const docs = await api("documents");
  const row = (d) => {
    const done = d.pages_checked + d.pages_draft;
    return `<tr ${STATIC ? "" : `class="click" data-doc="${esc(d.track)}/${esc(d.document_id)}"`}><td><b>${esc(d.document_id)}</b><div class="small muted">${esc(d.title)}</div></td>
      <td>${trackPill(d.track)}</td><td>${esc(d.doc_type)}</td><td>${esc(d.department)}</td><td>${esc(d.split)}</td>
      <td class="num">${d.page_count}</td><td class="num">${done}${d.pages_checked ? ` <span class="small muted">(${d.pages_checked} checked)</span>` : ""}${d.pages_marked ? ` <span class="small muted">+${d.pages_marked} picked</span>` : ""}</td>
      <td>${d.has_records ? '<span class="pill ok">records</span>' : ""}</td></tr>`;
  };
  $app.innerHTML = `<div class="toolbar"><h1 style="margin:0">Documents</h1>${STATIC ? "" : '<a class="btn" href="#/second">Second annotator</a>'}</div>
    <p class="lead">Every PDF is pinned by its SHA-256 so labels are never scored against another revision. Closed-track PDFs are copied into the confidential folder and never committed.${STATIC ? " This copy lists the open track only; the closed track's documents are named nowhere outside the BAM cluster." : ""}</p>
    <div class="scroll"><table class="grid"><tr><th>Document</th><th>Track</th><th>Type</th><th>Department</th><th>Split</th><th class="num">Pages</th><th class="num">Annotated</th><th></th></tr>
      ${docs.map(row).join("") || `<tr><td colspan="8" class="muted">No documents yet.</td></tr>`}</table></div>
    ${STATIC ? "" : `<h2>Add a PDF</h2>
    <div class="panel pad"><div class="form">
      <label class="f">PDF file<input type="file" id="f-file" accept="application/pdf"></label>
      <label class="f">Track<select id="f-track"><option value="closed">closed (internal report)</option><option value="open">open (publishable)</option></select></label>
      <label class="f">Document ID<input id="f-id" placeholder="e.g. dept3-report-001"></label>
      <label class="f">Title<input id="f-title"></label>
      <label class="f">Type<select id="f-type"><option>report</option><option>certificate</option><option>paper</option><option>standard</option><option>drawing</option></select></label>
      <label class="f">Department<input id="f-dept" placeholder="e.g. 3.3"></label>
      <label class="f">Family<input id="f-family" placeholder="same family = same split"></label>
      <label class="f">Language<select id="f-lang"><option>en</option><option>de</option></select></label>
      <label class="f">Split<select id="f-split"><option>dev</option><option>test</option></select></label>
      <button class="btn primary" id="f-add">Add document</button>
    </div><p class="small muted">The file goes only to this machine's benchmark folder. Use lowercase letters, digits and dashes for the ID.</p></div>`}`;
  $app.querySelectorAll("tr[data-doc]").forEach((tr) => (tr.onclick = () => (location.hash = "#/doc/" + tr.dataset.doc)));
  if (STATIC) return;
  document.getElementById("f-add").onclick = async () => {
    const file = document.getElementById("f-file").files[0];
    const id = document.getElementById("f-id").value.trim();
    if (!file || !id) return toast("Pick a PDF and give it an ID");
    const q = new URLSearchParams({
      track: document.getElementById("f-track").value, document_id: id, title: document.getElementById("f-title").value,
      doc_type: document.getElementById("f-type").value, department: document.getElementById("f-dept").value,
      family_id: document.getElementById("f-family").value, language: document.getElementById("f-lang").value,
      split: document.getElementById("f-split").value,
    });
    try {
      await api("documents?" + q, { method: "POST", body: file, headers: { "Content-Type": "application/pdf" } });
      toast("Added " + id);
      documents();
    } catch (e) { toast(e.message); }
  };
}

async function docDetail(track, id) {
  const d = await api(`documents/${track}/${encodeURIComponent(id)}`);
  const pages = Array.from({ length: d.page_count }, (_, i) => i + 1).map((p) => {
    const st = d.page_status[p];
    return `<a class="${st}" href="#/annotate/${track}/${encodeURIComponent(id)}/${p}"><img loading="lazy" src="/api/documents/${track}/${encodeURIComponent(id)}/pages/${p}.png?dpi=60" alt="Page ${p}">
      <div class="cap"><span>Page ${p}</span><span class="pill ${st}">${st === "marked" ? "picked" : st}</span></div></a>`;
  }).join("");
  $app.innerHTML = `<p class="small"><a href="#/documents">← Documents</a></p>
    <h1>${esc(d.title || d.document_id)}</h1><p>${trackPill(track)} <span class="muted small">${esc(d.document_id)} · ${d.page_count} pages · ${esc(d.doc_type)} · family ${esc(d.family_id)} · ${esc(d.split)} · sha256 ${esc(d.sha256.slice(0, 12))}…</span></p>
    ${d.notes ? `<p class="muted">${esc(d.notes)}</p>` : ""}
    <h2>Pages</h2>
    <div class="panel pad"><div class="toolbar">
      <label class="small">Pick pages to annotate <input id="m-pages" placeholder="e.g. 1, 4, 7, 18, 28" size="22"></label>
      <button class="btn primary" id="m-mark">Pick</button><button class="btn" id="m-unmark">Drop pick</button></div>
      <p class="small muted">Pick 4 to 6 pages, one of each kind the report has. A draft-only run on the Runs page then drafts every picked page, and you correct the drafts here. Dropping a pick never removes text you wrote.</p></div>
    <p class="small muted">Blue is picked, amber is draft, green is checked. Click a page to annotate it.</p>
    <div class="pages">${pages}</div>
    ${d.records ? `<h2>Measurement records (E5)</h2><p class="small muted">${d.records.records.length} records · ${esc(d.records.annotation_status)}</p>` : ""}`;
  const mark = async (marked) => {
    const pages = document.getElementById("m-pages").value.split(/[\s,;]+/).filter(Boolean).map(Number);
    if (!pages.length || pages.some((n) => !Number.isInteger(n))) return toast("Give page numbers like 1, 4, 7");
    try {
      const r = await api(`documents/${track}/${encodeURIComponent(id)}/mark`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pages, marked }) });
      toast(`${marked ? "Picked" : "Dropped"} ${r.changed.length} page${r.changed.length === 1 ? "" : "s"}`);
      docDetail(track, id);
    } catch (e) { toast(e.message); }
  };
  document.getElementById("m-mark").onclick = () => mark(true);
  document.getElementById("m-unmark").onclick = () => mark(false);
}

// ---------- Annotate ----------
function sanitize(html) {
  const allowed = new Set(["TABLE", "THEAD", "TBODY", "TR", "TD", "TH", "SUP", "SUB", "B", "I", "EM", "STRONG", "BR", "P", "H1", "H2", "H3", "H4", "UL", "OL", "LI", "SPAN", "CODE", "PRE"]);
  const doc = new DOMParser().parseFromString(`<div>${html}</div>`, "text/html");
  const walk = (n) => {
    for (const c of [...n.childNodes]) {
      if (c.nodeType === 1) {
        if (!allowed.has(c.tagName)) { c.replaceWith(...c.childNodes); walk(n); return; }
        for (const a of [...c.attributes]) if (!["colspan", "rowspan", "class"].includes(a.name)) c.removeAttribute(a.name);
        walk(c);
      }
    }
  };
  walk(doc.body.firstChild);
  return doc.body.firstChild.innerHTML;
}
function renderMarkdown(md) {
  const blocks = [];
  md = md.replace(/<table[\s\S]*?<\/table>/gi, (m) => { blocks.push(m); return `\n@@B${blocks.length - 1}@@\n`; });
  md = md.replace(/\$\$([\s\S]+?)\$\$/g, (_, f) => { blocks.push(`<span class="formula">${esc(f.trim())}</span>`); return `\n@@B${blocks.length - 1}@@\n`; });
  const out = md.split(/\n{2,}/).map((para) => {
    const p = para.trim();
    if (!p) return "";
    const b = p.match(/^@@B(\d+)@@$/);
    if (b) return blocks[+b[1]];
    const h = p.match(/^(#{1,4})\s+(.*)$/);
    if (h) return `<h${h[1].length + 1}>${h[2]}</h${h[1].length + 1}>`;
    if (/^\|.*\|/.test(p)) {
      const rows = p.split("\n").filter((l) => !/^\s*\|?\s*:?-{2,}/.test(l))
        .map((l) => "<tr>" + l.trim().replace(/^\||\|$/g, "").split("|").map((c) => `<td>${c.trim()}</td>`).join("") + "</tr>");
      return `<table>${rows.join("")}</table>`;
    }
    return `<p>${p.replace(/@@B(\d+)@@/g, (_, i) => blocks[+i]).replace(/\n/g, "<br>")}</p>`;
  }).join("");
  return sanitize(out);
}

async function annotate(track, id, page) {
  page = +page;
  const [d, ann, systems] = await Promise.all([
    api(`documents/${track}/${encodeURIComponent(id)}`),
    api(`documents/${track}/${encodeURIComponent(id)}/pages/${page}/annotation`),
    api("systems"),
  ]);
  const base = `#/annotate/${track}/${encodeURIComponent(id)}/`;
  const opts = (xs, cur) => xs.map(([v, l]) => `<option value="${v}" ${v === cur ? "selected" : ""}>${l}</option>`).join("");
  const KIND = [["", "kind…"], ["cover", "cover"], ["prose", "prose"], ["table", "table"], ["figure", "figure"], ["form", "form"], ["formula", "formula"], ["mixed", "mixed"]];
  const LANG = [["", "language…"], ["en", "English"], ["de", "German"], ["en+de", "English + German"]];
  let draftSource = null; // set when a prefill replaces the text; sent with the next save
  const srcOpts = [`<option value="pdftotext">Poppler text</option>`]
    .concat(systems.map((s) => `<option value="run:${esc(s.id)}">Latest run: ${esc(s.name || s.id)}</option>`)).join("");
  $app.innerHTML = `<p class="small"><a href="#/doc/${track}/${encodeURIComponent(id)}">← ${esc(d.title || id)}</a></p>
    <div class="toolbar"><h1 style="margin:0">Page ${page} of ${d.page_count}</h1> ${trackPill(track)}
      <span style="flex:1"></span>
      <a class="btn" href="#/compare/${track}/${encodeURIComponent(id)}/${page}">Compare models</a>
      <a class="btn" href="${base}${Math.max(1, page - 1)}">← Prev</a><a class="btn" href="${base}${Math.min(d.page_count, page + 1)}">Next →</a></div>
    <div class="annot">
      <div class="img"><img src="/api/documents/${track}/${encodeURIComponent(id)}/pages/${page}.png?dpi=130" alt="Page ${page}"></div>
      <div>
        <div class="toolbar">
          <select id="a-src">${srcOpts}</select><button class="btn" id="a-prefill">Prefill</button>
          <span style="flex:1"></span>
          <label class="small muted">Status <select id="a-status"><option value="marked">picked</option><option value="draft">draft</option><option value="checked">checked</option><option value="skip">skip</option></select></label>
        </div>
        <div class="toolbar">
          <select id="a-kind" title="What kind of page this is">${opts(KIND, ann.kind || "")}</select>
          <select id="a-lang" title="Language of the page">${opts(LANG, ann.lang || "")}</select>
          <span class="small muted">${ann.draft_source ? "first draft from " + esc(ann.draft_source) : ""}</span>
          <span style="flex:1"></span>
          <input id="a-who" placeholder="Annotator" size="10" value="${esc(ann.annotator || store.get("annotator", ""))}">
          <button class="btn primary" id="a-save">Save</button>
        </div>
        <textarea id="a-md" spellcheck="false" placeholder="Page content as Markdown. Tables as HTML <table>, display formulas as $$...$$. Leave out running headers, footers and page numbers.">${esc(ann.markdown || "")}</textarea>
        <input id="a-notes" placeholder="Notes (optional)" style="width:100%;margin-top:8px" value="${esc(ann.notes || "")}">
        <p class="small muted">Last saved: ${esc(ann.updated || "never")} ${ann.annotator ? "by " + esc(ann.annotator) : ""}. Ctrl+S saves.</p>
        <h2>Preview</h2><div class="panel preview" id="a-prev"></div>
      </div>
    </div>`;
  const ta = document.getElementById("a-md"), prev = document.getElementById("a-prev");
  document.getElementById("a-status").value = ann.status === "todo" || (ann.status === "marked" && !ann.markdown) ? "draft" : ann.status;
  const refresh = () => (prev.innerHTML = renderMarkdown(ta.value));
  ta.oninput = refresh;
  refresh();
  document.getElementById("a-prefill").onclick = async () => {
    if (ta.value.trim() && !confirmReplace()) return;
    try {
      const r = await api(`documents/${track}/${encodeURIComponent(id)}/pages/${page}/draft?source=${encodeURIComponent(document.getElementById("a-src").value)}`);
      ta.value = r.markdown;
      draftSource = r.draft_source;
      refresh();
      toast("Prefilled. Correct it against the page image before saving.");
    } catch (e) { toast(e.message); }
  };
  const save = async () => {
    const who = document.getElementById("a-who").value.trim();
    store.set("annotator", who);
    try {
      await api(`documents/${track}/${encodeURIComponent(id)}/pages/${page}/annotation`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ markdown: ta.value, status: document.getElementById("a-status").value, annotator: who,
          notes: document.getElementById("a-notes").value, kind: document.getElementById("a-kind").value,
          lang: document.getElementById("a-lang").value, draft_source: draftSource }),
      });
      toast("Saved page " + page);
    } catch (e) { toast(e.message); }
  };
  document.getElementById("a-save").onclick = save;
  document.onkeydown = (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); save(); } };
}
// Inline confirmation instead of a blocking browser dialog.
function confirmReplace() {
  const btn = document.getElementById("a-prefill");
  if (btn.dataset.armed) { delete btn.dataset.armed; btn.textContent = "Prefill"; return true; }
  btn.dataset.armed = "1";
  btn.textContent = "Replace text? Click again";
  setTimeout(() => { delete btn.dataset.armed; btn.textContent = "Prefill"; }, 4000);
  return false;
}

// ---------- Runs ----------
let poll;
async function runs() {
  const [systems, jobs] = await Promise.all([api("systems"), api("jobs")]);
  const running = jobs.some((j) => j.status === "running");
  const rows = systems.map((s) => `<tr><td><b>${esc(s.name || s.id)}</b><div class="small muted">${esc(s.model || s.kind)}</div></td>
    <td>${esc(s.params || "")}</td><td>${esc(s.license || "")}</td><td>${esc(s.gpu || "")}</td>
    <td>${s.available ? '<span class="pill ok">ready</span>' : `<span class="pill no" title="${esc(s.reason)}">not ready</span><div class="small muted">${esc(s.reason)}</div>`}</td>
    <td style="white-space:nowrap"><button class="btn" data-run="${esc(s.id)}" data-track="open" ${!s.available || running ? "disabled" : ""}>Run open</button>
      <button class="btn" data-run="${esc(s.id)}" data-track="closed" ${!s.available || running ? "disabled" : ""}>Run closed</button></td></tr>`).join("");
  const jobRows = jobs.map((j) => `<div class="panel pad" style="margin-bottom:8px"><b>${esc(j.system)}</b> on ${trackPill(j.track)}
      <span class="pill ${j.status === "done" ? "ok" : j.status === "failed" ? "draft" : ""}">${esc(j.status)}</span>${j.draft_only ? ' <span class="pill marked">draft only</span>' : ""}
      <span class="small muted">${esc(j.started)}${j.overall !== undefined && j.overall !== null ? " · overall " + pct(j.overall) : ""}</span>
      ${j.error ? `<div class="note small">${esc(j.error)}</div>` : ""}
      <div class="log">${esc(j.log.slice(-12).join("\n"))}</div></div>`).join("");
  $app.innerHTML = `<h1>Runs</h1>
    <p class="lead">A run predicts every annotated page, then scores it. A draft-only run predicts every picked page and scores nothing; use it to get first drafts to correct. vLLM systems need a model server running on this machine or the GPU node; see <code>slurm/</code> in the repository.</p>
    <p><label><input type="checkbox" id="r-draft"> Draft only: write first drafts for picked pages, no scores</label></p>
    <div class="scroll"><table class="grid"><tr><th>System</th><th>Params</th><th>License</th><th>GPU memory</th><th>Status</th><th></th></tr>${rows}</table></div>
    <h2>Recent runs</h2>${jobRows || `<p class="muted">No runs since the dashboard started. Command-line runs show up on the leaderboard.</p>`}`;
  $app.querySelectorAll("button[data-run]").forEach((b) => (b.onclick = async () => {
    try {
      await api("jobs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ system: b.dataset.run, track: b.dataset.track, draft_only: document.getElementById("r-draft").checked }) });
      toast("Run started");
      runs();
    } catch (e) { toast(e.message); }
  }));
  clearTimeout(poll);
  if (running) poll = setTimeout(() => { if (location.hash.startsWith("#/runs")) runs(); }, 1500);
}


// ---------- Models ----------
const CAP_LABEL = { tables: "Tables", formulas: "Formulas", handwriting: "Handwriting", german: "German", layout: "Layout boxes" };
let modelsTrack = store.get("modelsTrack", "closed");
async function models() {
  const m = await api("models");
  const mark = (v) => (v === true ? '<span class="yes" title="claimed by the publisher">✓</span>' : v === false ? '<span class="muted">✗</span>' : '<span class="muted">?</span>');
  const status = (s) => {
    const r = s.results[modelsTrack];
    if (r) return `<span class="pill ok">scored</span>`;
    if (STATIC) return `<span class="pill">no result here</span>`;
    if (s.seconds_per_page[modelsTrack] != null) return `<span class="pill marked">drafted</span>`;
    if (s.weights_downloaded === false) return `<span class="pill no" title="Download the weights on the login node">no weights</span>`;
    return s.available ? `<span class="pill">ready</span>` : `<span class="pill no" title="${esc(s.reason)}">not ready</span>`;
  };
  // One line of reason: the status note, else why a failed system failed, else why it is not ready.
  const why = (s) => s.status_note || (s.status === "failed" ? (s.failure?.[modelsTrack] || s.failure?.open || s.failure?.closed)?.error : "")
    || (!s.available && !s.results.open && !s.results.closed ? s.reason : "") || "";
  const counts = ["active", "pending", "failed", "superseded", "withdrawn"].map((k) => [m.systems.filter((s) => s.status === k).length, k]).filter(([n]) => n).map(([n, k]) => `${n} ${k}`).join(", ");
  const draw = () => {
    const rows = [...m.systems].sort((a, b) => (b.results[modelsTrack]?.overall ?? -1) - (a.results[modelsTrack]?.overall ?? -1));
    const body = rows.map((s) => {
      const r = s.results[modelsTrack];
      const kind = (k) => (r?.by_kind?.[k] !== undefined ? pct(r.by_kind[k]) : "—");
      const sp = s.seconds_per_page[modelsTrack];
      return `<tr>
        <td><b><a href="#/system/${esc(s.id)}">${esc(s.name || s.id)}</a></b>
          <div class="small muted">${esc(s.publisher || "")}${s.released ? " · " + esc(s.released) : ""}</div></td>
        <td class="num">${esc(s.params || "")}</td><td class="small">${esc(s.license || "")}</td><td class="small">${esc(s.slice || s.gpu || "")}</td>
        ${m.capabilities.map((c) => `<td class="cap">${mark(s.handles[c])}</td>`).join("")}
        <td class="num"><b>${r ? pct(r.overall) : "—"}</b></td><td class="num">${r ? pct(r.tables) : "—"}</td><td class="num">${r ? pct(r.formulas) : "—"}</td>
        <td class="num">${kind("figure")}</td><td class="num">${sp != null ? sp.toFixed(1) : "—"}</td>
        <td>${statusPill(s.status)} ${status(s)}${r && r.publishable === false ? ' <span class="pill draft" title="Fewer than 20 pages: internal only">internal</span>' : ""}${why(s) ? `<div class="small muted why">${esc(why(s))}</div>` : ""}</td></tr>`;
    }).join("");
    const watch = m.watchlist.map((w) => `<tr><td><b>${esc(w.name)}</b><div class="small muted">${esc(w.publisher || "")}</div></td>
      <td class="num">${esc(w.params || "")}</td><td class="small">${esc(w.license || "")}</td><td>${esc(w.reason)}</td></tr>`).join("");
    $app.innerHTML = `<h1>Models</h1>
      <p class="lead">Every system in the benchmark, with what its publisher says it handles next to what it scored here. Ticks are claims, not results. All of them run on BAM hardware with open weights.</p>
      <div class="tabs"><button data-t="open" class="${modelsTrack === "open" ? "on" : ""}">Open track scores</button><button data-t="closed" class="${modelsTrack === "closed" ? "on" : ""}">Closed track scores</button></div>
      <p class="small muted">${esc(counts)}</p>
      <div class="scroll"><table class="grid models"><tr><th>Model</th><th class="num">Size</th><th>License</th><th>GPU</th>
        ${m.capabilities.map((c) => `<th class="cap">${CAP_LABEL[c]}</th>`).join("")}
        <th class="num">Overall</th><th class="num">Tables</th><th class="num">Formulas</th><th class="num">Figures</th><th class="num" title="seconds per page, newest run">s / page</th><th>Status</th></tr>${body}</table></div>
      <p class="small muted">Scores are percentages over the annotated pages of the ${modelsTrack} track. Figures is the overall score on pages tagged as figure. Status: scored, drafted (ran in draft-only mode), ready, or no weights downloaded yet.</p>
      ${watch ? `<h2>Watch list</h2><p class="small muted">Promising models that are not in the benchmark yet, and why.</p>
        <div class="scroll"><table class="grid"><tr><th>Model</th><th class="num">Size</th><th>License</th><th>Why not yet</th></tr>${watch}</table></div>` : ""}`;
    $app.querySelectorAll("[data-t]").forEach((b) => (b.onclick = () => { modelsTrack = b.dataset.t; store.set("modelsTrack", modelsTrack); draw(); }));
  };
  draw();
}

// ---------- Compare ----------
let cmpMode = store.get("cmpMode", "rendered");
async function compare(track, id, page) {
  page = +page;
  const c = await api(`compare/${track}/${encodeURIComponent(id)}/${page}`);
  const hidden = new Set(JSON.parse(store.get("cmpHide", "[]")));
  const base = `#/compare/${track}/${encodeURIComponent(id)}/`;
  const g = c.gold;
  const hasGold = !!g.markdown;
  const diffHtml = (ops) => ops === null ? '<p class="muted small">Page too long for a word diff.</p>'
    : `<div class="diff">${ops.map(([op, t]) => op === "eq" ? esc(t) : `<${op}>${esc(t)}</${op}>`).join(" ")}</div>`;
  const tablesOf = (md) => (md.match(/<table[\s\S]*?<\/table>/gi) || []);
  const col = (sys) => {
    const sc = sys.score;
    const tabs = sc?.tables.length ? sc.tables.map((t) => pct(t)).join(", ") : "—";
    let body;
    if (cmpMode === "diff" && hasGold) {
      const t = tablesOf(sys.markdown);
      body = diffHtml(sys.diff) + (t.length ? `<h3>Tables</h3>${t.map((x) => `<div class="preview">${renderMarkdown(x)}</div>`).join("")}` : "");
    } else body = `<div class="preview">${renderMarkdown(sys.markdown)}</div>`;
    return `<div class="ccol"><div class="chead"><b>${esc(sys.name)}</b>
        <div class="small muted">${esc(sys.run_id)}${sys.draft_only ? ' · <span class="pill marked">draft only</span>' : ""}</div>
        ${sc ? `<div class="cscore"><span title="E1 text">Text <b>${pct(sc.text)}</b></span><span title="TEDS per gold table">Tables <b>${tabs}</b></span>${sc.formulas.length ? `<span>Formulas <b>${sc.formulas.map(pct).join(", ")}</b></span>` : ""}</div>` : ""}
        ${sys.drafted_gold ? '<div class="note small">The gold for this page started from this model\'s draft, so its score here is flattered.</div>' : ""}</div>${body}</div>`;
  };
  const shown = c.systems.filter((s) => !hidden.has(s.id));
  const chips = c.systems.map((s) => `<label class="chip"><input type="checkbox" data-sys="${esc(s.id)}" ${hidden.has(s.id) ? "" : "checked"}> ${esc(s.name)}</label>`).join("");
  $app.innerHTML = `<p class="small"><a href="#/doc/${track}/${encodeURIComponent(id)}">← ${esc(id)}</a> · <a href="#/annotate/${track}/${encodeURIComponent(id)}/${page}">Annotate this page</a></p>
    <div class="toolbar"><h1 style="margin:0">Compare page ${page} of ${c.page_count}</h1> ${trackPill(track)}
      ${g.kind ? `<span class="pill">${esc(g.kind)}</span>` : ""}${g.lang ? `<span class="pill">${esc(g.lang)}</span>` : ""}
      <span style="flex:1"></span>
      <div class="tabs" style="margin:0"><button data-m="rendered" class="${cmpMode === "rendered" ? "on" : ""}">Rendered</button><button data-m="diff" class="${cmpMode === "diff" ? "on" : ""}" ${hasGold ? "" : "disabled title=\"Needs gold text for this page\""}>Differences</button></div>
      <a class="btn" href="${base}${Math.max(1, page - 1)}">← Prev</a><a class="btn" href="${base}${Math.min(c.page_count, page + 1)}">Next →</a></div>
    ${c.systems.length ? `<div class="chips">${chips}</div>` : `<div class="note">No system has run on this page yet. Pick it on the document page and start a draft-only run.</div>`}
    ${cmpMode === "diff" && hasGold ? `<p class="small muted"><del>Struck red</del> is in the gold but missing from the model. <ins>Green</ins> is what the model wrote that the gold does not have. Tables are scored separately with TEDS.</p>` : ""}
    <div class="cmp">
      <div class="ccol scan"><div class="chead"><b>Page image</b></div><img src="/api/documents/${track}/${encodeURIComponent(id)}/pages/${page}.png?dpi=130" alt="Page ${page}"></div>
      <div class="ccol"><div class="chead"><b>Gold</b><div class="small muted">${hasGold ? esc(g.status) + (g.draft_source ? " · first draft from " + esc(g.draft_source) : "") : "no gold text yet"}</div></div>
        ${hasGold ? `<div class="preview">${renderMarkdown(g.markdown)}</div>` : `<p class="muted small" style="padding:0 12px">Scores and differences appear once this page has gold text.</p>`}</div>
      ${shown.map(col).join("")}
    </div>`;
  $app.querySelectorAll("[data-m]").forEach((b) => (b.onclick = () => { cmpMode = b.dataset.m; store.set("cmpMode", cmpMode); compare(track, id, page); }));
  $app.querySelectorAll("input[data-sys]").forEach((cb) => (cb.onchange = () => {
    cb.checked ? hidden.delete(cb.dataset.sys) : hidden.add(cb.dataset.sys);
    store.set("cmpHide", JSON.stringify([...hidden]));
    compare(track, id, page);
  }));
}

// ---------- Router ----------
async function route() {
  clearTimeout(poll);
  document.onkeydown = null;
  const parts = (location.hash.slice(2) || "overview").split("/").map(decodeURIComponent);
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("active", a.dataset.nav === parts[0] ||
    (parts[0] === "doc" || parts[0] === "annotate" || parts[0] === "compare" || parts[0] === "second" || parts[0] === "agree") && a.dataset.nav === "documents" || (parts[0] === "system" || parts[0] === "versus") && a.dataset.nav === "leaderboard" || parts[0] === "changelog" && a.dataset.nav === "about"));
  try {
    if (STATIC && ["doc", "annotate", "compare", "runs", "second", "agree"].includes(parts[0])) {
      $app.innerHTML = `<div class="note">This view needs the dashboard on the BAM cluster. The hosted copy is read-only.</div>`;
    } else if (parts[0] === "leaderboard") await leaderboard();
    else if (parts[0] === "system") await systemDetail(parts[1]);
    else if (parts[0] === "documents") await documents();
    else if (parts[0] === "doc") await docDetail(parts[1], parts[2]);
    else if (parts[0] === "annotate") await annotate(parts[1], parts[2], parts[3]);
    else if (parts[0] === "compare") await compare(parts[1], parts[2], parts[3]);
    else if (parts[0] === "models") await models();
    else if (parts[0] === "runs") await runs();
    else if (PAGES[parts[0]]) await PAGES[parts[0]](...parts.slice(1));
    else await overview();
  } catch (e) {
    $app.innerHTML = `<div class="note">Could not load this view: ${esc(e.message)}</div>`;
  }
  window.scrollTo(0, 0);
}
if (STATIC) document.querySelector('nav a[data-nav="runs"]')?.remove();
window.addEventListener("hashchange", route);
// pages.js loads after this file and must have registered its views before the first route.
window.addEventListener("DOMContentLoaded", route);
