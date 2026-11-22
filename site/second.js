// Blind second annotator: pick pages, label them without the first label in view, then compare.
// Loaded after app.js and uses its helpers ($app, api, esc, pct, store, toast, trackPill, renderMarkdown).
// The labelling view never asks for the first label. The comparison route refuses until the second
// label is saved as checked, so the page cannot show it earlier either.
"use strict";

const AG_METRICS = [["overall", "Overall"], ["e1_text", "E1 Text"], ["e2_table_teds", "E2 Tables"], ["e3_formula", "E3 Formulas"], ["numbers_recall", "Numbers"]];
const agPages = (n) => `${n} page${n === 1 ? "" : "s"}`;
const agRange = (a, k) => (a.pages < 2 ? "one page so far" : a.ci95?.[k] ? `${pct(a.ci95[k][0])}–${pct(a.ci95[k][1])}` : "");
const internalPill = (t, a) => (t === "closed" && a && a.publishable === false ? ' <span class="pill draft" title="Fewer than 20 pages: internal only">internal</span>' : "");

// Tiles for the five headline figures, each with its 95% interval.
function agTiles(a) {
  return AG_METRICS.map(([k, label]) => {
    const tip = k === "numbers_recall" ? ` title="Recall: the share of the first label's numbers that the second label holds, digit for digit. Precision is ${pct(a.numbers_precision)}."` : "";
    return `<div class="tile"${tip}><div class="k">${label}</div><div class="v">${pct(a[k])}</div><div class="s">${agRange(a, k)}</div></div>`;
  }).join("");
}
const agSentence = (a) => `Two people agree at ${pct(a.overall)} overall on ${agPages(a.pages)}. A system that scores close to that is within the noise of the labels.`;

// Overview tiles, one per track that has an agreement figure. Old overview files have none.
function agreeTile(ag) {
  return ["open", "closed"].filter((t) => ag?.[t]).map((t) => {
    const a = ag[t];
    const range = a.pages < 2 ? "one page so far" : a.ci95?.overall ? `95% range ${pct(a.ci95.overall[0])}–${pct(a.ci95.overall[1])}` : "";
    return `<div class="tile"><div class="k">Two annotators agree · ${t}</div><div class="v">${pct(a.overall)}${internalPill(t, a)}</div>
      <div class="s">${[range, agPages(a.pages)].filter(Boolean).join(" · ")}</div></div>`;
  }).join("");
}
// One muted line above the leaderboard table.
function agreeLine(ag, track) {
  const a = ag?.[track];
  if (!a) return "";
  return `<p class="small muted">Two annotators agree at ${pct(a.overall)} overall on ${agPages(a.pages)}${a.pages > 1 && a.ci95?.overall ? ` (95% range ${pct(a.ci95.overall[0])}–${pct(a.ci95.overall[1])})` : ""}${internalPill(track, a)}. A system close to that is within the noise of the labels.</p>`;
}

const secLink = (r) => `#/second/${r.track || secTrack}/${encodeURIComponent(r.document_id)}/${r.page}`;
let secTrack = store.get("secTrack", "open");
const jsonBody = (method, obj) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(obj) });

// ---------- Hub: #/second ----------
PAGES.second = async (track, id, page) => {
  if (id && page) return secLabel(track, id, +page);
  if (["open", "closed"].includes(track)) { secTrack = track; store.set("secTrack", track); }
  const t = secTrack;
  const [data, docs] = await Promise.all([api(`second/${t}`), api(`documents?track=${t}`)]);
  const title = Object.fromEntries(docs.map((d) => [d.document_id, d.title]));
  const q = data.queue, a = data.agreement;
  const rows = q.map((r) => `<tr><td><b>${esc(r.document_id)}</b><div class="small muted">${esc(title[r.document_id] || "")}</div></td>
    <td class="num">${r.page}</td><td>${esc(r.kind)}</td><td><span class="pill ${r.status}">${r.status === "marked" ? "picked" : r.status}</span></td>
    <td>${esc(r.annotator) || "—"}</td>
    <td class="nowrap">${r.status === "checked" ? `<a href="#/agree/${t}/${encodeURIComponent(r.document_id)}/${r.page}">Compare</a>`
      : `<a href="${secLink({ ...r, track: t })}">Label</a>`}${r.status === "marked" ? ` · <a href="#" data-drop="${esc(r.document_id)}|${r.page}">Drop</a>` : ""}</td></tr>`).join("");
  const perPage = a?.per_page?.length ? `<h2>Page by page</h2><div class="scroll"><table class="grid"><tr><th>Document</th><th class="num">Page</th><th>Kind</th>
    <th class="num">Overall</th><th class="num">Text</th><th class="num">Tables</th><th class="num">Formulas</th><th class="num">Numbers</th><th></th></tr>
    ${a.per_page.map((r) => `<tr><td>${esc(r.document_id)}</td><td class="num">${r.page}</td><td>${esc(r.kind)}</td><td class="num">${pct(r.overall)}</td><td class="num">${pct(r.text)}</td>
      <td class="num">${r.tables.length ? r.tables.map(pct).join(", ") : "—"}</td><td class="num">${r.formulas.length ? r.formulas.map(pct).join(", ") : "—"}</td>
      <td class="num">${pct(r.numbers)}</td><td><a href="#/agree/${t}/${encodeURIComponent(r.document_id)}/${r.page}">Compare</a></td></tr>`).join("")}</table></div>` : "";
  $app.innerHTML = `<p class="small"><a href="#/documents">← Documents</a></p>
    <h1>Second annotator</h1>
    <p class="lead">A second person labels a sample of pages without seeing the first label. The two labels are scored against each other with the benchmark's own scorer. The result is how far two people agree, which is also the best any system can be expected to reach.</p>
    <ol class="steps">
      <li><b>Pick pages.</b> The pick spreads over page kinds and documents, and only uses pages that already have a first label.</li>
      <li><b>Label from the page.</b> The second person opens a picked page and writes what is printed there, without opening the first label.</li>
      <li><b>Save it as checked.</b> At that moment a copy of the first label is kept for the comparison.</li>
      <li><b>Compare.</b> Both labels, the differences and the scores appear. Correcting the first label later does not change the agreement figure.</li>
    </ol>
    <div class="tabs"><button data-t="open" class="${t === "open" ? "on" : ""}">Open track</button><button data-t="closed" class="${t === "closed" ? "on" : ""}">Closed track</button></div>
    ${t === "closed" ? `<div class="note closed small">Closed-track document ids are shown here on this machine only. Only the overall agreement leaves it, and only when at least 20 pages back it.</div>` : ""}
    <h2>Pick pages</h2>
    <div class="toolbar"><label class="small muted">How many <input id="s-n" type="number" min="1" max="200" value="10" style="width:5em"></label>
      <button class="btn primary" id="s-pick">Pick pages</button>
      <span class="small muted">Pages that already have a second label are not picked again.</span></div>
    <h2>Queue</h2>
    ${q.length ? `<div class="scroll"><table class="grid"><tr><th>Document</th><th class="num">Page</th><th>Kind</th><th>Status</th><th>Annotator</th><th></th></tr>${rows}</table></div>`
      : `<p class="muted">No pages picked on this track yet.</p>`}
    <h2>Agreement</h2>
    ${a ? `<p>${esc(agSentence(a))}${internalPill(t, a)}</p>
      <div class="tiles dtiles">${agTiles(a)}</div>
      <p class="small muted">The first label is the reference and the second label is scored like a system's output. Intervals are 95%, from resampling the checked pages; ${a.pages < 2 ? "they appear once two pages are checked." : "more checked pages narrow them."}</p>${perPage}`
      : `<p class="muted">Nothing to show until a second label is saved as checked.</p>`}`;
  $app.querySelectorAll(".tabs [data-t]").forEach((b) => (b.onclick = () => (location.hash = `#/second/${b.dataset.t}`)));
  document.getElementById("s-pick").onclick = async () => {
    try {
      const r = await api(`second/${t}/pick`, jsonBody("POST", { n: +document.getElementById("s-n").value }));
      toast(`Picked ${agPages(r.picked.length)}`);
      PAGES.second(t);
    } catch (e) { toast(e.message); }
  };
  $app.querySelectorAll("[data-drop]").forEach((el) => (el.onclick = async (ev) => {
    ev.preventDefault();
    const [d, p] = el.dataset.drop.split("|");
    try {
      await api(`second/${t}/unpick`, jsonBody("POST", { document_id: d, page: +p }));
      PAGES.second(t);
    } catch (e) { toast(e.message); }
  }));
};

// ---------- Blind labelling: #/second/<track>/<id>/<page> ----------
async function secLabel(track, id, page) {
  const e = encodeURIComponent(id);
  // Not the document route: it also carries the first label's measurement records.
  const [docs, sec, systems, data] = await Promise.all([
    api(`documents?track=${track}`), api(`documents/${track}/${e}/pages/${page}/second`), api("systems"), api(`second/${track}`)]);
  const d = docs.find((x) => x.document_id === id);
  if (!d) throw new Error(`No document ${id} on the ${track} track`);
  const q = data.queue, at = q.findIndex((r) => r.document_id === id && r.page === page);
  const step = (i) => {
    const r = q[i];
    return r ? `<a class="btn" href="${secLink({ ...r, track })}">${i < at ? "← Prev" : "Next →"}</a>` : `<button class="btn" disabled>${i < at ? "← Prev" : "Next →"}</button>`;
  };
  const dis = (label) => `<button class="btn" disabled>${label}</button>`;
  let draftSource = null;
  const srcOpts = [`<option value="pdftotext">Poppler text</option>`]
    .concat(systems.map((s) => `<option value="run:${esc(s.id)}">Latest run: ${esc(s.name || s.id)}</option>`)).join("");
  const done = sec.status === "checked";
  $app.innerHTML = `<p class="small"><a href="#/second/${track}">← Second annotator</a></p>
    <div class="toolbar"><h1 style="margin:0">Page ${page} of ${d.page_count}</h1> ${trackPill(track)} <span class="small muted">${esc(d.title || id)}</span>
      <span style="flex:1"></span>
      ${at > 0 ? step(at - 1) : dis("← Prev")}${at >= 0 && at < q.length - 1 ? step(at + 1) : dis("Next →")}</div>
    <div class="note small blind">Label what is printed on the page. Do not open the first label of this page until yours is saved as checked.</div>
    <div class="annot">
      <div class="img"><img src="/api/documents/${track}/${e}/pages/${page}.png?dpi=130" alt="Page ${page}"></div>
      <div>
        <div class="toolbar">
          <select id="s-src">${srcOpts}</select><button class="btn" id="s-prefill">Prefill</button>
          <span style="flex:1"></span>
          <label class="small muted">Status <select id="s-status"><option value="draft">draft</option><option value="checked">checked</option></select></label>
        </div>
        <div class="toolbar">
          <span class="small muted">${sec.draft_source ? "started from " + esc(sec.draft_source) : ""}</span>
          <span style="flex:1"></span>
          <input id="s-who" placeholder="Annotator" size="10" value="${esc(sec.annotator || store.get("annotator2", ""))}">
          <button class="btn primary" id="s-save">Save</button>
        </div>
        <textarea id="s-md" spellcheck="false" placeholder="Page content as Markdown. Tables as HTML <table>, display formulas as $$...$$. Leave out running headers, footers and page numbers.">${esc(sec.markdown || "")}</textarea>
        <input id="s-notes" placeholder="Notes (optional)" style="width:100%;margin-top:8px" value="${esc(sec.notes || "")}">
        <p class="small muted">Last saved: ${esc(sec.updated || "never")} ${sec.annotator ? "by " + esc(sec.annotator) : ""}. Ctrl+S saves.</p>
        <p class="small" id="s-after">${done ? `<a href="#/agree/${track}/${e}/${page}">Compare with the first label</a>` : ""}</p>
        <h2>Preview</h2><div class="panel preview" id="s-prev"></div>
      </div>
    </div>`;
  const ta = document.getElementById("s-md"), prev = document.getElementById("s-prev"), btn = document.getElementById("s-prefill");
  document.getElementById("s-status").value = done ? "checked" : "draft";
  const refresh = () => (prev.innerHTML = renderMarkdown(ta.value));
  ta.oninput = refresh;
  refresh();
  btn.onclick = async () => {
    if (ta.value.trim() && !btn.dataset.armed) {  // ask once before replacing text
      btn.dataset.armed = "1";
      btn.textContent = "Replace text? Click again";
      setTimeout(() => { delete btn.dataset.armed; btn.textContent = "Prefill"; }, 4000);
      return;
    }
    delete btn.dataset.armed;
    btn.textContent = "Prefill";
    try {
      const r = await api(`documents/${track}/${e}/pages/${page}/second/draft?source=${encodeURIComponent(document.getElementById("s-src").value)}`);
      ta.value = r.markdown;
      draftSource = r.draft_source;
      refresh();
      toast("Prefilled. Correct it against the page image before saving.");
    } catch (err) { toast(err.message); }
  };
  const save = async () => {
    const who = document.getElementById("s-who").value.trim();
    store.set("annotator2", who);
    try {
      const status = document.getElementById("s-status").value;
      await api(`documents/${track}/${e}/pages/${page}/second`, jsonBody("PUT", {
        markdown: ta.value, status, annotator: who, notes: document.getElementById("s-notes").value, draft_source: draftSource }));
      toast("Saved page " + page);
      document.getElementById("s-after").innerHTML = status === "checked" ? `<a href="#/agree/${track}/${e}/${page}">Compare with the first label</a>` : "";
    } catch (err) { toast(err.message); }
  };
  document.getElementById("s-save").onclick = save;
  document.onkeydown = (ev) => { if ((ev.ctrlKey || ev.metaKey) && ev.key === "s") { ev.preventDefault(); save(); } };
}

// ---------- Comparison: #/agree/<track>/<id>/<page> ----------
PAGES.agree = async (track, id, page) => {
  page = +page;
  const e = encodeURIComponent(id);
  let c;
  try { c = await api(`documents/${track}/${e}/pages/${page}/agree`); }
  catch (err) {
    $app.innerHTML = `<p class="small"><a href="#/second/${track}">← Second annotator</a></p><h1>Compare page ${page}</h1>
      <div class="note">${esc(err.message)} <a href="#/second/${track}/${e}/${page}">Back to your label</a>.</div>`;
    return;
  }
  const sc = c.score;
  const diff = c.diff === null ? '<p class="muted small">Page too long for a word diff.</p>'
    : `<div class="diff">${c.diff.map(([op, t]) => (op === "eq" ? esc(t) : `<${op}>${esc(t)}</${op}>`)).join(" ")}</div>`;
  const num = sc.numbers.gold ? `${sc.numbers.matched} of ${sc.numbers.gold}` : "—";
  $app.innerHTML = `<p class="small"><a href="#/second/${track}">← Second annotator</a> · <a href="#/annotate/${track}/${e}/${page}">Edit the first label</a></p>
    <div class="toolbar"><h1 style="margin:0">Agreement on page ${page} of ${c.page_count}</h1> ${trackPill(track)}</div>
    <div class="cscore" style="font-size:13px;margin:8px 0"><span>Overall <b>${pct(sc.overall)}</b></span><span>Text <b>${pct(sc.text)}</b></span>
      <span>Tables <b>${sc.tables.length ? sc.tables.map(pct).join(", ") : "—"}</b></span><span>Formulas <b>${sc.formulas.length ? sc.formulas.map(pct).join(", ") : "—"}</b></span>
      <span title="Numbers of the first label that the second label holds, digit for digit">Numbers <b>${num}</b></span></div>
    <div class="note small">The agreement figure uses the first label as it was when the two were compared${c.first.updated ? ` (${esc(c.first.updated.slice(0, 10))})` : ""}, so editing the first label now does not change it.
      ${c.first_live !== null ? "The first label has been edited since; the live version is shown below the columns." : ""}</div>
    <div class="cmp">
      <div class="ccol scan"><div class="chead"><b>Page image</b></div><img src="/api/documents/${track}/${e}/pages/${page}.png?dpi=130" alt="Page ${page}"></div>
      <div class="ccol"><div class="chead"><b>First label</b><div class="small muted">${esc(c.first.annotator) || "—"}</div></div><div class="preview">${renderMarkdown(c.first.markdown)}</div></div>
      <div class="ccol"><div class="chead"><b>Second label</b><div class="small muted">${esc(c.second.annotator) || "—"}${c.second.draft_source ? " · started from " + esc(c.second.draft_source) : ""}</div></div><div class="preview">${renderMarkdown(c.second.markdown)}</div></div>
    </div>
    <h2>Differences in the text</h2>
    <p class="small muted"><del>Struck red</del> is in the first label but not the second. <ins>Green</ins> is what only the second label has. Tables and formulas are scored separately.</p>
    <div class="panel">${diff}</div>
    ${c.first_live !== null ? `<h2>First label now</h2><div class="panel preview">${renderMarkdown(c.first_live)}</div>` : ""}`;
};
