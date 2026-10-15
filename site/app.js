// BAM Extraction Benchmark dashboard. Plain JavaScript, no build step, works offline.
"use strict";

const TARGETS = { open: 60, closed: 60 }; // annotated pages planned for the Nov 30 release
const METRICS = [
  ["overall", "Overall", "Mean of E1, E2 and E3"],
  ["e1_text", "E1 Text", "1 minus normalised edit distance"],
  ["e2_table_teds", "E2 Tables", "TEDS, structure and cell content"],
  ["e2_table_teds_struct", "E2 Structure", "TEDS, structure only"],
  ["e3_formula", "E3 Formulas", "1 minus normalised edit distance on LaTeX"],
  ["e5_record_f1", "E5 Records", "Exact-record F1 on measurement rows"],
];

const $app = document.getElementById("app");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pct = (x) => (x === null || x === undefined ? "—" : (100 * x).toFixed(1));
const store = {
  get(k, d) { try { return localStorage.getItem(k) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
};

async function api(path, opts = {}) {
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
      <div class="tile"><div class="k">Release</div><div class="v">Nov 30</div><div class="s">v0.1, annotated pages frozen before the final runs</div></div>
    </div>
    <h2>Leaderboard, top systems</h2>
    ${lb.length ? `<div class="scroll"><table class="grid"><tr><th>System</th><th class="num">Open overall</th><th class="num">Closed overall</th></tr>${top}</table></div>
      <p class="small"><a href="#/leaderboard">Full leaderboard</a></p>` : `<p class="muted">No results yet. Start one under <a href="#/runs">Runs</a>.</p>`}
    <div class="note small">All scores so far use <b>draft</b> labels written by one annotator. They show that the pipeline works; they are not yet benchmark results.</div>`;
}

// ---------- Leaderboard ----------
let lbTrack = store.get("lbTrack", "open");
let lbSort = "overall";
async function leaderboard() {
  const rows = await api("leaderboard");
  const draw = () => {
    const have = rows.filter((r) => r[lbTrack]);
    have.sort((a, b) => (b[lbTrack].scores[lbSort] ?? -1) - (a[lbTrack].scores[lbSort] ?? -1));
    const best = {};
    for (const [k] of METRICS) best[k] = Math.max(...have.map((r) => r[lbTrack].scores[k] ?? -1));
    const head = METRICS.map(([k, label, tip]) => `<th class="num sort" data-k="${k}" title="${esc(tip)}">${label}${lbSort === k ? " ↓" : ""}</th>`).join("");
    const body = have.map((r) => {
      const s = r[lbTrack];
      const cells = METRICS.map(([k]) => `<td class="num ${have.length > 1 && s.scores[k] !== null && s.scores[k] === best[k] ? "best" : ""}">${pct(s.scores[k])}</td>`).join("");
      return `<tr class="click" data-sys="${esc(r.system)}"><td><b>${esc(r.card.name || r.system)}</b><div class="small muted">${esc(r.card.params || "")} · ${esc(r.card.license || "")}</div></td>
        ${cells}<td class="num">${s.counts.pages}${s.publishable === false ? ' <span class="pill draft" title="Fewer than 20 pages: internal only">internal</span>' : ""}</td><td class="small muted">${esc(s.finished.slice(0, 10))}</td></tr>`;
    }).join("");
    $app.innerHTML = `<h1>Leaderboard</h1>
      <p class="lead">Scores are percentages, higher is better. Click a column to sort and a row for details. Every row was produced by a local run with a pinned system card.</p>
      <div class="tabs"><button data-t="open" class="${lbTrack === "open" ? "on" : ""}">Open track</button><button data-t="closed" class="${lbTrack === "closed" ? "on" : ""}">Closed track</button></div>
      ${lbTrack === "closed" ? `<div class="note closed small">Closed-track numbers are aggregates over confidential reports. Only publish a number when it is backed by at least 20 pages.</div>` : ""}
      ${have.length ? `<div class="scroll"><table class="grid"><tr><th>System</th>${head}<th class="num">Pages</th><th>Run</th></tr>${body}</table></div>`
        : `<p class="muted">No ${lbTrack}-track results yet.</p>`}`;
    $app.querySelectorAll("[data-t]").forEach((b) => (b.onclick = () => { lbTrack = b.dataset.t; store.set("lbTrack", lbTrack); draw(); }));
    $app.querySelectorAll("th[data-k]").forEach((th) => (th.onclick = () => { lbSort = th.dataset.k; draw(); }));
    $app.querySelectorAll("tr[data-sys]").forEach((tr) => (tr.onclick = () => (location.hash = "#/system/" + tr.dataset.sys)));
  };
  draw();
}

// ---------- System detail ----------
async function systemDetail(id) {
  const rows = await api("leaderboard");
  const r = rows.find((x) => x.system === id);
  if (!r) { $app.innerHTML = `<p>No results for ${esc(id)} yet.</p>`; return; }
  const card = Object.entries(r.card).filter(([k]) => !["id"].includes(k))
    .map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(typeof v === "object" ? JSON.stringify(v) : v)}</td></tr>`).join("");
  let docs = "";
  try {
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
  const sc = (t) => r[t] ? METRICS.map(([k, l]) => `<div class="tile"><div class="k">${l}</div><div class="v">${pct(r[t].scores[k])}</div></div>`).join("") : "";
  $app.innerHTML = `<p class="small"><a href="#/leaderboard">← Leaderboard</a></p><h1>${esc(r.card.name || id)}</h1>
    ${r.open ? `<h2>Open track ${trackPill("open")}</h2><div class="tiles">${sc("open")}</div>` : ""}
    ${r.closed ? `<h2>Closed track ${trackPill("closed")}</h2><div class="tiles">${sc("closed")}</div>` : ""}
    ${docs ? `<h2>Per document, open track</h2><div class="scroll"><table class="grid"><tr><th>Document</th><th class="num">Pages</th><th class="num">E1 Text</th><th class="num">E2 Tables</th><th class="num">E5 Records</th></tr>${docs}</table></div>` : ""}
    <h2>System card</h2><div class="scroll"><table class="grid">${card}</table></div>
    <h2>Run environment</h2><div class="scroll"><table class="grid">
      ${["open", "closed"].filter((t) => r[t]).map((t) => `<tr><th>${t}</th><td>${esc(r[t].environment.gpu)} · Python ${esc(r[t].environment.python)} · ${r[t].runtime_s}s · run ${esc(r[t].run_id)}</td></tr>`).join("")}
    </table></div>`;
}

// ---------- Documents ----------
async function documents() {
  const docs = await api("documents");
  const row = (d) => {
    const done = d.pages_checked + d.pages_draft;
    return `<tr class="click" data-doc="${esc(d.track)}/${esc(d.document_id)}"><td><b>${esc(d.document_id)}</b><div class="small muted">${esc(d.title)}</div></td>
      <td>${trackPill(d.track)}</td><td>${esc(d.doc_type)}</td><td>${esc(d.department)}</td><td>${esc(d.split)}</td>
      <td class="num">${d.page_count}</td><td class="num">${done}${d.pages_checked ? ` <span class="small muted">(${d.pages_checked} checked)</span>` : ""}</td>
      <td>${d.has_records ? '<span class="pill ok">records</span>' : ""}</td></tr>`;
  };
  $app.innerHTML = `<h1>Documents</h1>
    <p class="lead">Every PDF is pinned by its SHA-256 so labels are never scored against another revision. Closed-track PDFs are copied into the confidential folder and never committed.</p>
    <div class="scroll"><table class="grid"><tr><th>Document</th><th>Track</th><th>Type</th><th>Department</th><th>Split</th><th class="num">Pages</th><th class="num">Annotated</th><th></th></tr>
      ${docs.map(row).join("") || `<tr><td colspan="8" class="muted">No documents yet.</td></tr>`}</table></div>
    <h2>Add a PDF</h2>
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
    </div><p class="small muted">The file goes only to this machine's benchmark folder. Use lowercase letters, digits and dashes for the ID.</p></div>`;
  $app.querySelectorAll("tr[data-doc]").forEach((tr) => (tr.onclick = () => (location.hash = "#/doc/" + tr.dataset.doc)));
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
      <div class="cap"><span>Page ${p}</span><span class="pill ${st}">${st}</span></div></a>`;
  }).join("");
  $app.innerHTML = `<p class="small"><a href="#/documents">← Documents</a></p>
    <h1>${esc(d.title || d.document_id)}</h1><p>${trackPill(track)} <span class="muted small">${esc(d.document_id)} · ${d.page_count} pages · ${esc(d.doc_type)} · family ${esc(d.family_id)} · ${esc(d.split)} · sha256 ${esc(d.sha256.slice(0, 12))}…</span></p>
    ${d.notes ? `<p class="muted">${esc(d.notes)}</p>` : ""}
    <h2>Pages</h2><p class="small muted">Green is checked, amber is draft. Click a page to annotate it. Mark pages you do not want scored as skip.</p>
    <div class="pages">${pages}</div>
    ${d.records ? `<h2>Measurement records (E5)</h2><p class="small muted">${d.records.records.length} records · ${esc(d.records.annotation_status)}</p>` : ""}`;
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
  const srcOpts = [`<option value="pdftotext">Poppler text</option>`]
    .concat(systems.map((s) => `<option value="run:${esc(s.id)}">Latest run: ${esc(s.name || s.id)}</option>`)).join("");
  $app.innerHTML = `<p class="small"><a href="#/doc/${track}/${encodeURIComponent(id)}">← ${esc(d.title || id)}</a></p>
    <div class="toolbar"><h1 style="margin:0">Page ${page} of ${d.page_count}</h1> ${trackPill(track)}
      <span style="flex:1"></span>
      <a class="btn" href="${base}${Math.max(1, page - 1)}">← Prev</a><a class="btn" href="${base}${Math.min(d.page_count, page + 1)}">Next →</a></div>
    <div class="annot">
      <div class="img"><img src="/api/documents/${track}/${encodeURIComponent(id)}/pages/${page}.png?dpi=130" alt="Page ${page}"></div>
      <div>
        <div class="toolbar">
          <select id="a-src">${srcOpts}</select><button class="btn" id="a-prefill">Prefill</button>
          <span style="flex:1"></span>
          <label class="small muted">Status <select id="a-status"><option value="draft">draft</option><option value="checked">checked</option><option value="skip">skip</option></select></label>
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
  document.getElementById("a-status").value = ann.status === "todo" ? "draft" : ann.status;
  const refresh = () => (prev.innerHTML = renderMarkdown(ta.value));
  ta.oninput = refresh;
  refresh();
  document.getElementById("a-prefill").onclick = async () => {
    if (ta.value.trim() && !confirmReplace()) return;
    try {
      const r = await api(`documents/${track}/${encodeURIComponent(id)}/pages/${page}/draft?source=${encodeURIComponent(document.getElementById("a-src").value)}`);
      ta.value = r.markdown;
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
        body: JSON.stringify({ markdown: ta.value, status: document.getElementById("a-status").value, annotator: who, notes: document.getElementById("a-notes").value }),
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
      <span class="pill ${j.status === "done" ? "ok" : j.status === "failed" ? "draft" : ""}">${esc(j.status)}</span>
      <span class="small muted">${esc(j.started)}${j.overall !== undefined && j.overall !== null ? " · overall " + pct(j.overall) : ""}</span>
      ${j.error ? `<div class="note small">${esc(j.error)}</div>` : ""}
      <div class="log">${esc(j.log.slice(-12).join("\n"))}</div></div>`).join("");
  $app.innerHTML = `<h1>Runs</h1>
    <p class="lead">A run predicts every page of every annotated document, then scores it. vLLM systems need a model server running on this machine or the GPU node; see <code>slurm/</code> in the repository.</p>
    <div class="scroll"><table class="grid"><tr><th>System</th><th>Params</th><th>License</th><th>GPU memory</th><th>Status</th><th></th></tr>${rows}</table></div>
    <h2>Recent runs</h2>${jobRows || `<p class="muted">No runs since the dashboard started. Command-line runs show up on the leaderboard.</p>`}`;
  $app.querySelectorAll("button[data-run]").forEach((b) => (b.onclick = async () => {
    try {
      await api("jobs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ system: b.dataset.run, track: b.dataset.track }) });
      toast("Run started");
      runs();
    } catch (e) { toast(e.message); }
  }));
  clearTimeout(poll);
  if (running) poll = setTimeout(() => { if (location.hash.startsWith("#/runs")) runs(); }, 1500);
}

// ---------- About ----------
function about() {
  $app.innerHTML = `<h1>About this benchmark</h1>
  <div class="panel pad" style="max-width:820px">
  <p>Given a PDF page, a system writes the page as Markdown: text in reading order, tables as HTML, display formulas as LaTeX. It is scored per element type, so a parser that reads text well but breaks tables cannot hide behind an average.</p>
  <table class="grid"><tr><th>Task</th><th>Metric</th></tr>
  <tr><td>E1 Text</td><td>1 minus normalised Levenshtein distance on whitespace-normalised text, tables and formulas removed</td></tr>
  <tr><td>E2 Tables</td><td>TEDS (tree edit distance similarity) per gold table, greedy one-to-one matching; TEDS-S ignores cell text</td></tr>
  <tr><td>E3 Formulas</td><td>1 minus normalised edit distance on normalised LaTeX</td></tr>
  <tr><td>E5 Records</td><td>Exact-record F1 on certificate measurement rows: value, unit, expanded uncertainty, k, certified status, oxide, page. Uncertainty is never a tolerance</td></tr>
  <tr><td>Overall</td><td>Mean of E1, E2 and E3, as in OmniDocBench</td></tr></table>
  <h2>Rules</h2>
  <ul><li>Only open-weight models running on BAM hardware. No cloud APIs on the closed track.</li>
  <li>Closed-track PDFs, labels and raw outputs stay in <code>data/closed</code>, which Git ignores and the pre-commit hook guards.</li>
  <li>Splits are by document family, never by page.</li>
  <li>Labels are drafts until a page is re-checked; drafts are marked everywhere they are used.</li></ul>
  </div>`;
}

// ---------- Router ----------
async function route() {
  clearTimeout(poll);
  document.onkeydown = null;
  const parts = (location.hash.slice(2) || "overview").split("/").map(decodeURIComponent);
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("active", a.dataset.nav === parts[0] ||
    (parts[0] === "doc" || parts[0] === "annotate") && a.dataset.nav === "documents" || parts[0] === "system" && a.dataset.nav === "leaderboard"));
  try {
    if (parts[0] === "leaderboard") await leaderboard();
    else if (parts[0] === "system") await systemDetail(parts[1]);
    else if (parts[0] === "documents") await documents();
    else if (parts[0] === "doc") await docDetail(parts[1], parts[2]);
    else if (parts[0] === "annotate") await annotate(parts[1], parts[2], parts[3]);
    else if (parts[0] === "runs") await runs();
    else if (parts[0] === "about") about();
    else await overview();
  } catch (e) {
    $app.innerHTML = `<div class="note">Could not load this view: ${esc(e.message)}</div>`;
  }
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", route);
route();
