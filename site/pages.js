// Views that only read data: system comparison, composition, changelog, about, footer.
// Loaded after app.js and uses its helpers ($app, api, esc, pct, STATIC, store, toast, trackPill).
"use strict";

// ---------- shared helpers ----------
const nameOf = (r) => r.card?.name || r.system;
const num = (x) => (x === null || x === undefined ? "—" : Number(x).toLocaleString("en-GB"));
// Signed difference in percentage points, with a real minus sign.
const signed = (x) => (x === null || x === undefined ? "—" : (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(100 * x).toFixed(1));
const isHttps = (u) => typeof u === "string" && /^https:\/\//i.test(u);

// ---------- Versus ----------
const VS_METRICS = [["overall", "Overall"], ["e1_text", "E1 Text"], ["e2_table_teds", "E2 Tables"], ["e3_formula", "E3 Formulas"], ["numbers_recall", "Numbers"]];

// A summary seen the fair way: without the pages whose labels started from the system's own draft.
function fairView(s) {
  const v = s.excluding_own_drafts;
  if (v) return v;
  return { ...s.scores, pages: s.counts?.pages ?? null, ci95: s.ci95 || null };
}

// The paired file is stored for the pair in string order; give it back from a's point of view.
function orient(p, swap) {
  if (!swap) return p;
  const metrics = {};
  for (const [k, m] of Object.entries(p.metrics)) {
    metrics[k] = { a: m.b, b: m.a, diff: m.diff === null ? null : -m.diff, ci95: m.ci95 ? [-m.ci95[1], -m.ci95[0]] : null };
  }
  return { ...p, a: p.b, b: p.a, metrics, pages_won: { a: p.pages_won.b, b: p.pages_won.a, tie: p.pages_won.tie } };
}

PAGES.versus = async (track, a, b) => {
  const rows = await api("leaderboard");
  const link = (t) => `#/versus/${t}/${encodeURIComponent(a)}/${encodeURIComponent(b)}`;
  const back = `<p class="small"><a href="#/leaderboard">← Leaderboard</a></p>`;
  const ra = rows.find((r) => r.system === a), rb = rows.find((r) => r.system === b);
  if (!["open", "closed"].includes(track) || !ra || !rb || a === b) {
    const why = a === b ? "Pick two different systems to compare."
      : !ra && !rb ? `Neither ${esc(a)} nor ${esc(b)} has a result yet.`
      : `${esc(!ra ? a : b)} has no result yet.`;
    $app.innerHTML = `${back}<h1>Comparison</h1><div class="note">${why} <a href="#/leaderboard">Back to the leaderboard</a>.</div>`;
    return;
  }
  const tracks = ["open", "closed"].filter((t) => ra[t] && rb[t]);
  const tabs = tracks.length > 1 ? `<div class="tabs">${tracks.map((t) => `<button data-t="${t}" class="${t === track ? "on" : ""}">${t === "open" ? "Open track" : "Closed track"}</button>`).join("")}</div>` : "";
  const head = `${back}<div class="vs-head"><h1><a href="#/system/${esc(a)}">${esc(nameOf(ra))}</a> <span class="muted">against</span> <a href="#/system/${esc(b)}">${esc(nameOf(rb))}</a></h1>
    <div class="vs-tools">${trackPill(track)}<a class="btn" href="#/versus/${track}/${encodeURIComponent(b)}/${encodeURIComponent(a)}">Swap</a></div></div>`;
  const wire = () => {
    $app.querySelectorAll(".tabs [data-t]").forEach((x) => (x.onclick = () => (location.hash = link(x.dataset.t))));
    const sel = document.getElementById("vs-b");
    if (sel) sel.onchange = () => (location.hash = `#/versus/${track}/${encodeURIComponent(a)}/${encodeURIComponent(sel.value)}`);
  };
  if (!ra[track] || !rb[track]) {
    const miss = [!ra[track] && nameOf(ra), !rb[track] && nameOf(rb)].filter(Boolean).map(esc).join(" and ");
    $app.innerHTML = `${head}${tabs}<div class="note">${miss} ${!ra[track] && !rb[track] ? "have" : "has"} no result on the ${track} track. ${tracks.length ? "" : ""}<a href="#/leaderboard">Back to the leaderboard</a>.</div>`;
    wire();
    return;
  }
  const sa = ra[track], sb = rb[track];
  const others = rows.filter((r) => r[track] && r.system !== a);
  const picker = `<label class="small muted vs-pick">Compare with <select id="vs-b">${others.map((r) => `<option value="${esc(r.system)}" ${r.system === b ? "selected" : ""}>${esc(nameOf(r))}</option>`).join("")}</select></label>`;
  const A = esc(nameOf(ra)), B = esc(nameOf(rb));

  // The paired file only exists for the pair in string order.
  const swap = a > b;
  let paired = null;
  try {
    const [x, y] = swap ? [b, a] : [a, b];
    paired = orient(await api(`versus/${track}/${encodeURIComponent(x)}/${encodeURIComponent(y)}`), swap);
  } catch { /* old runs, or a copy without per-page scores */ }

  const fa = fairView(sa), fb = fairView(sb);
  const publishable = paired ? paired.publishable !== false : sa.publishable !== false && sb.publishable !== false;
  const internal = track === "closed" && !publishable;

  // One row per metric.
  const read = (lo, hi) => (lo > 0 ? ["a", `${A} ahead`] : hi < 0 ? ["b", `${B} ahead`] : ["tie", "cannot tell apart"]);
  const metricRows = VS_METRICS.map(([k, label]) => {
    let va, vb, diff, interval, reading;
    if (paired && paired.metrics[k]) {
      const m = paired.metrics[k];
      va = m.a; vb = m.b; diff = m.diff;
      interval = m.ci95 ? `${signed(m.ci95[0])} to ${signed(m.ci95[1])}` : "—";
      reading = m.ci95 ? read(m.ci95[0], m.ci95[1]) : ["tie", "no interval recorded"];
    } else {
      va = fa[k]; vb = fb[k];
      diff = va === null || va === undefined || vb === null || vb === undefined ? null : va - vb;
      const ia = fa.ci95?.[k], ib = fb.ci95?.[k];
      interval = `<div>${A}: ${ia ? pct(ia[0]) + "–" + pct(ia[1]) : "—"}</div><div>${B}: ${ib ? pct(ib[0]) + "–" + pct(ib[1]) : "—"}</div>`;
      reading = diff === null ? ["tie", "—"] : !ia || !ib ? ["tie", "no interval recorded"]
        : ia[0] > ib[1] ? ["a", `ranges do not overlap: ${A} ahead`] : ib[0] > ia[1] ? ["b", `ranges do not overlap: ${B} ahead`] : ["tie", "ranges overlap: cannot tell apart"];
    }
    return `<tr><td><b>${label}</b></td><td class="num">${pct(va)}</td><td class="num">${pct(vb)}</td><td class="num">${signed(diff)}</td>
      <td class="num ${paired ? "ci" : "small muted"}">${interval}</td><td><span class="read ${reading[0]}">${reading[1]}</span></td></tr>`;
  }).join("");

  // Pages won, as a sentence and a three-part bar.
  let pagesBlock = "";
  if (paired) {
    const w = paired.pages_won, n = Math.max(1, w.a + w.b + w.tie);
    pagesBlock = `<h2>Page by page</h2>
      <p class="vs-sentence">${A} is better on <b>${w.a}</b> of ${paired.pages} pages, ${B} on <b>${w.b}</b>, ${w.tie} ${w.tie === 1 ? "is a tie" : "are ties"}.</p>
      <div class="split" role="img" aria-label="Pages won: ${w.a} ${A}, ${w.b} ${B}, ${w.tie} ties"><span class="a" style="width:${100 * w.a / n}%"></span><span class="t" style="width:${100 * w.tie / n}%"></span><span class="b" style="width:${100 * w.b / n}%"></span></div>
      <p class="small muted">${paired.pages} pages were compared. ${paired.excluded_own_drafts ? `${paired.excluded_own_drafts} ${paired.excluded_own_drafts === 1 ? "was" : "were"} left out because one of the two drafted ${paired.excluded_own_drafts === 1 ? "its" : "their"} labels.` : "None were left out for drafted labels."}</p>`;
  }
  const noPaired = paired ? "" : `<div class="note small">A paired comparison needs per-page scores, which are not available here. ${STATIC
    ? "In this read-only copy it is only available for the open track."
    : `On the cluster dashboard run <code>python3 -m bambench rescore --track ${esc(track)}</code> to add them.`} Until then each system is shown on its own, without the pages whose labels started from its own draft, and the reading only says whether the two 95% ranges overlap.</div>`;

  // Cost: lower is better.
  const costRows = [
    ["seconds_per_page", "Seconds per page", (x) => x.toFixed(1), "faster"],
    ["eur_per_1000_pages", "€ per 1,000 pages", (x) => x.toFixed(2), "cheaper"],
    ["output_tokens_per_page", "Tokens written per page", (x) => num(x), "fewer tokens"],
  ].map(([k, label, fmt, word]) => {
    const x = sa.cost?.[k], y = sb.cost?.[k];
    const has = (v) => v !== null && v !== undefined;
    let ratio = "—";
    if (has(x) && has(y)) {
      if (x === 0 && y === 0) ratio = "both free";
      else if (x === 0) ratio = `${A} is free`;
      else if (y === 0) ratio = `${B} is free`;
      else {
        const r = x < y ? y / x : x / y;
        ratio = r < 1.05 ? "about the same" : `${x < y ? A : B} is ${r.toFixed(1)} times ${word}`;
      }
    }
    return `<tr><td>${label}</td><td class="num">${has(x) ? fmt(x) : "—"}</td><td class="num">${has(y) ? fmt(y) : "—"}</td><td>${ratio}</td></tr>`;
  }).join("");

  // By page kind, all pages of each system.
  const kinds = [...new Set([...Object.keys(sa.by_kind || {}), ...Object.keys(sb.by_kind || {})])].sort();
  const kindRows = kinds.map((k) => {
    const x = sa.by_kind?.[k], y = sb.by_kind?.[k];
    return `<tr><td>${esc(k)}</td><td class="num">${x ? x.pages : "—"}</td><td class="num">${x ? pct(x.overall) : "—"}</td><td class="num">${y ? y.pages : "—"}</td><td class="num">${y ? pct(y.overall) : "—"}</td></tr>`;
  }).join("");

  const facts = [["Publisher", "publisher"], ["Released", "released"], ["Size", "params"], ["Licence", "license"], ["Slice", "slice"]]
    .map(([l, k]) => `<tr><th>${l}</th><td>${esc(ra.card[k] || "—")}</td><td>${esc(rb.card[k] || "—")}</td></tr>`).join("");

  $app.innerHTML = `${head}${tabs}
    <div class="toolbar">${picker}</div>
    ${internal ? `<div class="note closed small"><span class="pill draft">internal</span> Numbers backed by fewer than 20 pages are not for publication.</div>` : ""}
    ${noPaired}
    <div class="scroll"><table class="grid vs"><tr><th>Metric</th><th class="num"><span class="dot a"></span>${A}</th><th class="num"><span class="dot b"></span>${B}</th>
      <th class="num" title="${A} minus ${B}, in percentage points">Difference</th><th class="num">${paired ? "95% interval of the difference" : "95% range of each"}</th><th>Reading</th></tr>${metricRows}</table></div>
    <p class="small muted">Scores are percentages. Difference is ${A} minus ${B} in percentage points.${paired ? " A reading is only given when the 95% interval of the difference excludes zero." : ""}</p>
    ${pagesBlock}
    <h2>Speed and cost</h2>
    <div class="scroll"><table class="grid"><tr><th></th><th class="num">${A}</th><th class="num">${B}</th><th>Ratio</th></tr>${costRows}</table></div>
    ${kinds.length ? `<h2>By page kind</h2><div class="scroll"><table class="grid"><tr><th>Kind</th><th class="num">Pages ${A}</th><th class="num">Overall ${A}</th><th class="num">Pages ${B}</th><th class="num">Overall ${B}</th></tr>${kindRows}</table></div>
      <p class="small muted">All scored pages of each system, so the page counts can differ.</p>` : ""}
    <h2>System cards</h2>
    <div class="scroll"><table class="grid"><tr><th></th><th>${A}</th><th>${B}</th></tr>${facts}</table></div>`;
  wire();
};

// ---------- Data ----------
const LANG_NAME = { en: "English", de: "German", "en+de": "English and German" };
const STATUS_NAME = { checked: "checked", draft: "draft", marked: "picked, no label yet" };

// A list of label, bar and count, longest first. Rows are {label (html), n, title?, n2?}.
function barList(title, rows, opts = {}) {
  rows = rows.filter((r) => r.n > 0 || r.n2 > 0).sort((x, y) => y.n - x.n);
  if (!rows.length) return "";
  const max = Math.max(...rows.map((r) => Math.max(r.n, r.n2 || 0)));
  const body = rows.map((r) => `<div class="brow"><div class="bl" title="${esc(r.title || "")}">${r.label}</div>
    <div class="bt"><div class="bf" style="width:${100 * r.n / max}%"></div>${r.n2 !== undefined ? `<div class="bf two" style="width:${100 * r.n2 / max}%"></div>` : ""}</div>
    <div class="bn">${num(r.n)}${r.n2 !== undefined ? ` <span class="muted">· ${num(r.n2)}</span>` : ""}</div></div>`).join("");
  return `<div class="blist panel pad"><h3>${title}</h3>${opts.legend ? `<p class="small muted">${opts.legend}</p>` : ""}${body}</div>`;
}

function dataObservations(c, track) {
  const out = [];
  const lab = c.labelled || 0;
  if (!lab) return ["No page has a label yet."];
  const checked = c.by_status?.checked || 0;
  out.push(checked === 0 ? "No page has been checked yet. Every label is still a draft." : `${num(checked)} of ${num(lab)} labelled pages have been checked.`);
  const langs = Object.entries(c.by_lang || {}).sort((x, y) => y[1] - x[1]);
  if (langs.length) {
    const [l, n] = langs[0];
    out.push(n === lab ? `All ${num(lab)} labelled pages are ${LANG_NAME[l] || l}.` : `${num(n)} of ${num(lab)} labelled pages are ${LANG_NAME[l] || l}.`);
  }
  out.push(!c.second_labels ? "No page has a second label yet, so there is no agreement figure." : `${num(c.second_labels)} ${c.second_labels === 1 ? "page has" : "pages have"} a second label, which allows an agreement figure.`);
  if (c.pages > lab) out.push(`${num(lab)} of ${num(c.pages)} pages are labelled.`);
  return out.slice(0, 4);
}

function dataSection(c, track, sysIds) {
  const ent = (o) => Object.entries(o || {});
  const tiles = [["Documents", c.documents], ["Pages", c.pages], ["Labelled pages", c.labelled], ["Checked pages", c.by_status?.checked ?? 0],
    ["Report families", c.families], ["With a second label", c.second_labels]]
    .map(([k, v]) => `<div class="tile"><div class="k">${k}</div><div class="v">${num(v)}</div></div>`).join("");
  const src = ent(c.by_draft_source).map(([k, n]) => {
    const id = k.startsWith("run:") ? k.slice(4) : null;
    return { label: id ? (sysIds.has(id) ? `drafted by <a href="#/system/${esc(id)}">${esc(id)}</a>` : `drafted by ${esc(id)}`) : esc(k), n };
  });
  const lists = [
    barList("Page kind", ent(c.by_kind).map(([k, n]) => ({ label: esc(k), n }))),
    barList("Language", ent(c.by_lang).map(([k, n]) => ({ label: esc(LANG_NAME[k] || k), n }))),
    barList("Document type", ent(c.by_doc_type).map(([k, v]) => ({ label: esc(k), n: v.documents, n2: v.labelled })), { legend: "Documents · labelled pages" }),
    barList("Label status", ent(c.by_status).map(([k, n]) => ({ label: esc(STATUS_NAME[k] || k), n }))),
    barList("First draft source", src),
    barList("Split", ent(c.by_split).map(([k, n]) => ({ label: esc(k), n }))),
    barList("Rights status", ent(c.by_rights).map(([k, n]) => ({ label: esc(k.replace(/_/g, " ")), n })), { legend: "Documents" }),
    barList("Department", ent(c.by_department).map(([k, n]) => ({ label: esc(k), n }))),
    barList("Decade", ent(c.by_decade).map(([k, n]) => ({ label: esc(k), n }))),
  ].join("");
  const obs = dataObservations(c, track);
  return `<h2>${track === "open" ? "Open track" : "Closed track"} ${trackPill(track)}</h2>
    ${track === "closed" ? `<div class="note closed small">Only counts are shown. Document names stay inside BAM.</div>` : ""}
    <div class="tiles dtiles">${tiles}</div>
    <ul class="obs">${obs.map((o) => `<li>${esc(o)}</li>`).join("")}</ul>
    <div class="blists">${lists}</div>`;
}

PAGES.data = async () => {
  const [comp, lb] = await Promise.all([api("composition"), api("leaderboard").catch(() => [])]);
  const sysIds = new Set(lb.map((r) => r.system));
  $app.innerHTML = `<h1>Data</h1>
    <p class="lead">What the benchmark contains: how many documents and pages there are, which pages carry a label, and where the labels came from. Counts only.</p>
    ${comp.open ? dataSection(comp.open, "open", sysIds) : ""}
    ${comp.closed ? dataSection(comp.closed, "closed", sysIds) : `<h2>Closed track ${trackPill("closed")}</h2><p class="muted">The closed track's composition is not part of this copy yet.</p>`}`;
};

// ---------- Changelog ----------
// A small Markdown reader. Everything is escaped first; HTML comes only from the tags written here.
function mdInline(s) {
  const codes = [];
  let t = esc(String(s).replace(/\u0000/g, ""));
  t = t.replace(/`([^`]+)`/g, (_, c) => { codes.push(`<code>${c}</code>`); return `\u0000${codes.length - 1}\u0000`; });
  t = t.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, text, url) => (isHttps(url) ? `<a href="${url}" target="_blank" rel="noopener">${text}</a>` : text));
  t = t.replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>").replace(/\*([^*\s][^*]*?)\*/g, "<i>$1</i>");
  return t.replace(/\u0000(\d+)\u0000/g, (_, i) => codes[+i]);
}

function mdBlocks(md) {
  const out = [];
  let para = [], list = null;
  const flushPara = () => { if (para.length) out.push(`<p>${mdInline(para.join(" "))}</p>`); para = []; };
  const flushList = () => { if (list) out.push(`<ul>${list.map((i) => `<li>${mdInline(i.join(" "))}</li>`).join("")}</ul>`); list = null; };
  let blankAfterList = false;
  for (const raw of md.replace(/\r/g, "").split("\n")) {
    const line = raw.trimEnd();
    let m;
    if (!line.trim()) { flushPara(); blankAfterList = !!list; continue; }
    if ((m = line.match(/^(#{1,3})\s+(.*)$/))) { flushPara(); flushList(); out.push(`<h${m[1].length}>${mdInline(m[2])}</h${m[1].length}>`); continue; }
    if ((m = line.match(/^\s*[-*]\s+(.*)$/)) && !/^\*\*/.test(line.trim())) {
      flushPara(); (list = list || []).push([m[1]]); blankAfterList = false; continue;
    }
    if (list && !blankAfterList) { list[list.length - 1].push(line.trim()); continue; } // wrapped line of a list item
    flushList(); blankAfterList = false; para.push(line.trim());
  }
  flushPara(); flushList();
  return out.join("\n");
}

PAGES.changelog = async () => {
  const ab = await api("about");
  $app.innerHTML = `<div class="doc"><p class="small muted">Software version ${esc(ab.version)} · scorer version ${esc(ab.scorer)}</p>
    <div class="md">${mdBlocks(ab.changelog || "")}</div></div>`;
};

// ---------- About ----------
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); toast("Copied"); return; } catch { /* fall through */ }
  const ta = document.createElement("textarea");
  ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
  document.body.appendChild(ta); ta.select();
  try { document.execCommand("copy"); toast("Copied"); } catch { toast("Could not copy. Select the text and copy it."); }
  ta.remove();
}

PAGES.about = async (part) => {
  const ab = await api("about");
  const ext = (u) => (/^https?:\/\//i.test(u || "") ? ` target="_blank" rel="noopener"` : "");
  $app.innerHTML = `<h1>About this benchmark</h1>
    <div class="panel pad doc">
    <p>Given a PDF page, a system writes the page as Markdown: text in reading order, tables as HTML, display formulas as LaTeX. It is scored per element type, so a parser that reads text well but breaks tables cannot hide behind an average.</p>
    <div class="scroll"><table class="grid"><tr><th>Task</th><th>Metric</th></tr>
      <tr><td>E1 Text</td><td>1 minus normalised Levenshtein distance on whitespace-normalised text, tables and formulas removed</td></tr>
      <tr><td>E2 Tables</td><td>TEDS (tree edit distance similarity) per gold table, greedy one-to-one matching; TEDS-S ignores cell text</td></tr>
      <tr><td>E3 Formulas</td><td>1 minus normalised edit distance on normalised LaTeX</td></tr>
      <tr><td>E5 Records</td><td>Exact-record F1 on certificate measurement rows: value, unit, expanded uncertainty, k, certified status, oxide, page. Uncertainty is never a tolerance</td></tr>
      <tr><td>Numbers</td><td>Share of the printed numbers the output holds digit for digit. Not part of Overall</td></tr>
      <tr><td>Overall</td><td>Mean of E1, E2 and E3, as in OmniDocBench</td></tr>
      <tr><td>95% interval</td><td>From resampling the scored pages 1,000 times</td></tr></table></div>
    <h2>Rules</h2>
    <ul><li>Only open-weight models running on BAM hardware. No cloud APIs on the closed track.</li>
      <li>Closed-track PDFs, labels and raw outputs stay in <code>data/closed</code>, which Git ignores and the pre-commit hook guards.</li>
      <li>Splits are by document family, never by page.</li>
      <li>Labels are drafts until a page is re-checked; drafts are marked everywhere they are used.</li>
      <li>A system is ranked without the pages whose labels started from its own draft.</li></ul>
    <h2>Version</h2>
    <p>Software version ${esc(ab.version)}, scorer version ${esc(ab.scorer)}.</p>
    <h2 id="cite">How to cite</h2>
    <p>${esc(ab.citation?.text || "—")}</p>
    ${ab.citation?.cff ? `<details class="cff"><summary><span>CITATION.cff</span><button class="btn" id="cff-copy" type="button">Copy</button></summary><pre>${esc(ab.citation.cff)}</pre></details>` : ""}
    <h2>Licence</h2>
    <p>${ab.license ? esc(ab.license) : "No licence has been chosen yet. Until one is, the code and the labels may not be reused outside BAM."}</p>
    <h2>Contact</h2>
    <p>${ab.contact ? esc(ab.contact) : "No contact address has been set yet."}</p>
    <h2>More</h2>
    <p><a href="#/changelog">Changelog</a> · <a href="#/data">Data</a>${ab.repository ? ` · <a href="${esc(ab.repository)}"${ext(ab.repository)}>Repository</a>` : ""}</p>
    </div>`;
  const btn = document.getElementById("cff-copy");
  if (btn) btn.onclick = (e) => { e.preventDefault(); e.stopPropagation(); copyText(ab.citation.cff); };
  // The router scrolls to the top after the view returns, so jump afterwards.
  if (part === "cite") setTimeout(() => document.getElementById("cite")?.scrollIntoView(), 50);
};

// ---------- Footer ----------
async function footer() {
  const el = document.getElementById("foot");
  if (!el) return;
  try {
    let ab = null;
    try { ab = await api("about"); } catch { /* static links only */ }
    const ver = ab ? ` v${esc(ab.version)} · scorer ${esc(ab.scorer)}` : "";
    const built = STATIC && STATIC.built ? `<div>built ${esc(String(STATIC.built).slice(0, 10))}${STATIC.commit ? ` from commit <code>${esc(STATIC.commit)}</code>` : ""}</div>` : "";
    el.innerHTML = `<div>BAM Extraction Benchmark${ver} · <a href="#/changelog">Changelog</a> · <a href="#/about/cite">How to cite</a> · <a href="#/data">Data</a></div>${built}`;
  } catch { /* the footer never throws */ }
}
footer();
