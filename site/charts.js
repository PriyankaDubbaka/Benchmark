// Leaders at a glance, score against cost, ranked bars and score against size. Loaded after app.js,
// whose helpers (esc, pct, paramsB, placeLabels, shortName, store, LB_LANG) it uses. Plain SVG, no library.
"use strict";

// What kind of system a row is. Colour and marker shape both carry it, so it never rests on colour alone.
const DOC_VLM = /ocr|mineru|dots\.|paddle|chandra|nanonets|qianfan|lighton|granite-docling/i;
const TYPES = [
  ["doc", "Document VLM", "Trained for one job: page image in, Markdown, tables and LaTeX out"],
  ["gen", "General VLM", "General vision language model with the benchmark's page prompt"],
  ["pipe", "Pipeline or baseline", "No vision language model reads the page, or a layout pipeline around one"],
];
function modelType(r) {
  const c = r.card || {};
  if (c.kind === "mineru_vl" || c.kind === "glm_ocr") return "doc";
  if (c.kind !== "vllm") return "pipe";
  return DOC_VLM.test(`${r.system} ${c.name || ""}`) ? "doc" : "gen";
}
const typeLabel = (t) => TYPES.find(([k]) => k === t)?.[1] ?? t;
function marker(t, x, y, r = 5) {
  if (t === "doc") return `<path class="mk t-${t}" d="M${x} ${y - r * 1.3}L${x + r * 1.3} ${y}L${x} ${y + r * 1.3}L${x - r * 1.3} ${y}Z"/>`;
  if (t === "pipe") return `<rect class="mk t-${t}" x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}"/>`;
  return `<circle class="mk t-${t}" cx="${x}" cy="${y}" r="${r}"/>`;
}
const legendKey = (t) => `<svg class="key" viewBox="0 0 14 14" aria-hidden="true">${marker(t, 7, 7, 4.5)}</svg>`;

// Remembered chart choices.
const chS = {
  x: store.get("ch_x", "eur_per_1000_pages"), bar: store.get("ch_bar", "overall"),
  pareto: store.get("ch_pareto", "1") === "1", all: store.get("ch_all", "0") === "1", hide: new Set(store.get("ch_hide", "").split(",").filter(Boolean)),
};
const chSet = (k, v) => {
  chS[k] = v;
  store.set("ch_" + k, k === "hide" ? [...v].join(",") : typeof v === "boolean" ? (v ? "1" : "0") : v);
};
const X_AXES = [
  ["eur_per_1000_pages", "Cost", "€ per 1,000 pages", (x) => (x < 1 ? x.toFixed(2) : x < 10 ? x.toFixed(1) : x.toFixed(0))],
  ["seconds_per_page", "Time", "Seconds per page", (x) => (x < 10 ? x.toFixed(1) : x.toFixed(0))],
  ["output_tokens_per_page", "Tokens", "Output tokens per page", (x) => fmtN(Math.round(x))],
];
const BAR_METRICS = [
  ["overall", "Overall", true], ["e1_text", "Text", true], ["e2_table_teds", "Tables", true], ["e3_formula", "Formulas", true],
  ["numbers_recall", "Numbers", true], ["seconds_per_page", "Sec / page", false], ["eur_per_1000_pages", "€ / 1k pages", false],
];

// ---------- Leaders at a glance ----------
// One tile per question people ask first. Each names the system, its value and how close the next one is.
// A lead inside the 95% range of the runner-up is called a tie, because the benchmark cannot separate them yet.
function leaders(rows, track = "open", view = "all") {
  const items = rows.filter((r) => r[track]).map((r) => ({ r, s: r[track], p: lbPick(r[track], view) }))
    .filter((it) => it.p && it.p.scores.overall != null);
  if (items.length < 2) return "";
  const nm = (it) => it.r.card?.name || it.r.system;
  const link = (it) => `<a href="#/system/${encodeURIComponent(it.r.system)}">${esc(shortName(nm(it)))}</a>`;
  const top = Math.max(...items.map((it) => it.p.scores.overall));
  const near = items.filter((it) => it.p.scores.overall >= top - 0.05);
  const pick = (list, get, low = false) => list.map((it) => ({ it, v: get(it) })).filter((x) => x.v !== null && x.v !== undefined && Number.isFinite(x.v))
    .sort((a, b) => (low ? a.v - b.v : b.v - a.v));
  const tile = (k, ranked, fmt, how, note = "") => {
    if (!ranked.length) return "";
    const [a, b] = ranked;
    const type = modelType(a.it.r);
    return `<div class="lead-tile"><div class="k">${k}</div>
      <div class="who">${legendKey(type)}${link(a.it)}</div>
      <div class="val">${fmt(a.v)}</div>
      <div class="s">${b ? `then ${esc(shortName(nm(b.it)))} at ${fmt(b.v)}` : "no other system qualifies"}${note ? ` · ${note}` : ""}</div>
      <div class="how">${how}</div></div>`;
  };
  const sc = (k) => (it) => it.p.scores[k];
  const cost = (k) => (it) => (it.s.cost?.[k] > 0 ? it.s.cost[k] : null);
  const best = pick(items, sc("overall"));
  let tie = "";
  if (best[1]) {
    const iv = best[0].it.p.ci95?.overall, n = best.filter((x) => iv && x.v >= iv[0]).length - 1;
    tie = n > 0 ? `${n} more within its 95% range` : "";
  }
  const small = items.filter((it) => { const b = paramsB(it.r.card?.params); return b !== null && b <= 4; });
  const de = items.map((it) => ({ it, v: it.s.by_lang?.de?.pages >= FEW_PAGES ? it.s.by_lang.de.overall : null }));
  const p100 = (x) => `${pct(x)}`;
  const euro = (x) => `€${x < 1 ? x.toFixed(2) : x.toFixed(1)} <small>per 1k pages</small>`;
  const sec = (x) => `${x.toFixed(1)} s <small>per page</small>`;
  return `<div class="leaders">
    ${tile("Highest overall", best, p100, "Mean of text, tables and formulas", tie)}
    ${tile("Cheapest near the top", pick(near, cost("eur_per_1000_pages"), true), euro, "Within 5 points of the best overall")}
    ${tile("Fastest near the top", pick(near, cost("seconds_per_page"), true), sec, "Within 5 points of the best overall")}
    ${tile("Best small model", pick(small, sc("overall")), p100, "4 billion parameters or fewer")}
    ${tile("Best on tables", pick(items, sc("e2_table_teds")), p100, "TEDS, structure and cell content")}
    ${tile("Best on German pages", de.filter((x) => x.v !== null).sort((a, b) => b.v - a.v), p100, `Overall on German pages, ${FEW_PAGES} or more`)}
  </div>`;
}

// ---------- Shared bits ----------
const higher = (yes) => `<span class="dir">${yes ? "Higher is better" : "Lower is better"}</span>`;
function legend(types) {
  return `<div class="legend" role="group" aria-label="Show or hide a kind of system">${TYPES.filter(([k]) => types.has(k)).map(([k, l, tip]) =>
    `<button class="lg ${chS.hide.has(k) ? "off" : ""}" data-hide="${k}" title="${esc(tip)}. Click to ${chS.hide.has(k) ? "show" : "hide"}." aria-pressed="${!chS.hide.has(k)}">${legendKey(k)}${l}</button>`).join("")}</div>`;
}
const tipAttr = (lines) => `data-tip="${esc(lines.join("\n"))}"`;
function logTicks(lo, hi) {
  const out = [];
  for (let e = Math.floor(lo) - 1; e <= Math.ceil(hi); e++) for (const m of [1, 2, 5]) {
    const v = m * 10 ** e;
    if (Math.log10(v) >= lo && Math.log10(v) <= hi) out.push(v);
  }
  return out;
}
const tickLabel = (v) => (v >= 1000 ? fmtN(v) : v >= 1 ? String(v) : String(+v.toPrecision(1)));

// ---------- Score against cost, time or tokens ----------
// Log scale across. The shaded corner is above the median score and below the median cost of the systems
// shown. The step line joins the systems nothing else beats on both: higher score and lower cost.
function valueChart(points, xKey) {
  const [, , xName] = X_AXES.find(([k]) => k === xKey) || X_AXES[0];
  const all = points.filter((p) => p.y != null && p.x != null);
  const pts = all.filter((p) => p.x > 0);
  const zero = all.filter((p) => p.x === 0);
  if (pts.length < 2) return `<p class="small muted">Needs two systems with a measured ${esc(xName.toLowerCase())}.</p>`;
  const W = 760, H = 420, R = 24, T = 18, B = 48, L0 = 52, Z = zero.length ? 44 : 0, L = L0 + Z;
  const lo = Math.log10(Math.min(...pts.map((p) => p.x)) / 1.4), hi = Math.log10(Math.max(...pts.map((p) => p.x)) * 1.4);
  const ys = all.map((p) => p.y);
  const ymin = Math.max(0, Math.floor(Math.min(...ys) * 10 - 0.5) / 10), ymax = Math.min(1, Math.ceil(Math.max(...ys) * 10 + 0.3) / 10);
  const X = (x) => (x === 0 ? L0 + Z / 2 : L + ((Math.log10(x) - lo) / (hi - lo)) * (W - L - R));
  const Y = (y) => T + (1 - (y - ymin) / (ymax - ymin)) * (H - T - B);
  const med = (xs) => { const s = [...xs].sort((a, b) => a - b), m = Math.floor(s.length / 2); return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  const mx = med(pts.map((p) => p.x)), my = med(ys);
  const yt = []; for (let v = ymin; v <= ymax + 1e-9; v += 0.1) yt.push(+v.toFixed(1));
  const grid = yt.map((v) => `<line x1="${L0}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" class="gridline"/><text x="${L0 - 8}" y="${Y(v) + 4}" text-anchor="end">${Math.round(v * 100)}</text>`).join("")
    + logTicks(lo, hi).map((v) => `<text x="${X(v)}" y="${H - B + 18}" text-anchor="middle">${tickLabel(v)}</text>`).join("")
    + (Z ? `<text x="${X(0)}" y="${H - B + 18}" text-anchor="middle">0</text><line x1="${L - 6}" x2="${L - 6}" y1="${T}" y2="${H - B}" class="brk"/>` : "");
  const quad = `<rect class="quad" x="${L}" y="${T}" width="${Math.max(0, X(mx) - L)}" height="${Math.max(0, Y(my) - T)}"/>
    <text class="quadlabel" x="${L + 8}" y="${Y(my) - 8}">Higher score, ${xKey === "output_tokens_per_page" ? "fewer tokens" : xKey === "seconds_per_page" ? "faster" : "cheaper"}</text>
    <line class="med" x1="${X(mx)}" x2="${X(mx)}" y1="${T}" y2="${H - B}"/><line class="med" x1="${L}" x2="${W - R}" y1="${Y(my)}" y2="${Y(my)}"/>`;
  // Frontier: walk from cheapest to dearest and keep each point that beats every cheaper one.
  let best = -1;
  const front = [...all].sort((a, b) => a.x - b.x || b.y - a.y).filter((p) => (p.y > best ? ((best = p.y), true) : false));
  const path = front.map((p, i) => (i ? `H${X(p.x)} V${Y(p.y)}` : `M${X(p.x)} ${Y(p.y)}`)).join(" ");
  const named = new Set([...front, ...[...all].sort((a, b) => b.y - a.y).slice(0, 3)]);
  const order = [...all].sort((a, b) => b.y - a.y);
  const labelled = order.filter((p) => named.has(p));
  const boxes = all.map((p) => ({ x1: X(p.x) - 7, x2: X(p.x) + 7, y1: Y(p.y) - 7, y2: Y(p.y) + 7 }));
  boxes.push({ x1: L, x2: L + 170, y1: Y(my) - 22, y2: Y(my) });
  const picks = placeLabels(labelled.map((p) => ({ cx: X(p.x), cy: Y(p.y), label: shortName(p.name) })), boxes, W, L0);
  const lab = new Map(labelled.map((p, i) => [p, picks[i]]));
  const [, , , fmt] = X_AXES.find(([k]) => k === xKey) || X_AXES[0];
  const dots = order.reverse().map((p) => {
    const at = lab.get(p);
    return `<g class="pt ${front.includes(p) ? "front" : ""}" data-sys="${esc(p.sys)}" tabindex="0" aria-label="${esc(p.name)}" ${tipAttr([p.name, `${typeLabel(p.type)}${p.params ? " · " + p.params : ""}`, `Overall ${pct(p.y)}`, `${xName} ${fmt(p.x)}`])}>
      <circle class="hit" cx="${X(p.x)}" cy="${Y(p.y)}" r="11"/>${marker(p.type, X(p.x), Y(p.y))}
      ${at ? `<text x="${at[0]}" y="${at[1]}" text-anchor="${at[2]}">${esc(shortName(p.name))}</text>` : ""}</g>`;
  }).join("");
  return `<div class="scroll plot"><svg class="chart" data-chart="value" viewBox="0 0 ${W} ${H}" role="img" aria-label="Overall score against ${esc(xName.toLowerCase())}">
    ${quad}${grid}<line x1="${L0}" x2="${W - R}" y1="${H - B}" y2="${H - B}" class="axis"/>
    ${chS.pareto ? `<path class="step" d="${path}"/>` : ""}
    <text x="${(L + W - R) / 2}" y="${H - 8}" text-anchor="middle" class="label">${esc(xName)} (log scale, better to the left)</text>
    <text x="14" y="${(T + H - B) / 2}" text-anchor="middle" class="label" transform="rotate(-90 14 ${(T + H - B) / 2})">Overall</text>
    ${dots}</svg></div>`;
}

// ---------- Ranked bars for one metric ----------
const BAR_TOP = 15; // rows shown until "Show all" is ticked
function rankedBars(items, key, isScore) {
  const ranked = items.filter((p) => p.v != null && (isScore || p.v > 0)).sort((a, b) => (isScore ? b.v - a.v : a.v - b.v));
  if (ranked.length < 2) return `<p class="small muted">Needs two systems with this value.</p>`;
  const rows = chS.all ? ranked : ranked.slice(0, BAR_TOP);
  const W = 760, N = 188, R = 64, rowH = 22, T = 4, H = T + rows.length * rowH + 4;
  const max = isScore ? 1 : Math.max(...rows.map((p) => p.v)) * 1.05;
  const BW = (v) => Math.max(2, (v / max) * (W - N - R));
  const fmt = (v) => (isScore ? pct(v) : key === "eur_per_1000_pages" ? `€${v.toFixed(2)}` : `${v.toFixed(1)} s`);
  const grid = (isScore ? [0, 0.25, 0.5, 0.75, 1] : []).map((v) => `<line class="gridline" x1="${N + BW(v)}" x2="${N + BW(v)}" y1="${T}" y2="${H - 4}"/>`).join("");
  const bars = rows.map((p, i) => {
    const y = T + i * rowH;
    return `<g class="pt bar" data-sys="${esc(p.sys)}" tabindex="0" aria-label="${esc(p.name)}: ${fmt(p.v)}" ${tipAttr([p.name, typeLabel(p.type), fmt(p.v)])}>
      <rect class="hit" x="0" y="${y}" width="${W}" height="${rowH}"/>
      <text x="${N - 10}" y="${y + 15}" text-anchor="end" class="name">${esc(shortName(p.name))}</text>
      <rect class="mk t-${p.type}" x="${N}" y="${y + 4}" width="${BW(p.v)}" height="${rowH - 8}" rx="2"/>
      <text x="${N + BW(p.v) + 6}" y="${y + 15}" class="val">${fmt(p.v)}</text></g>`;
  }).join("");
  const more = ranked.length > BAR_TOP ? `<label class="chk"><input type="checkbox" data-all ${chS.all ? "checked" : ""}> Show all ${ranked.length}, not only the best ${BAR_TOP}</label>` : "";
  return `${more}<div class="scroll plot"><svg class="chart bars" data-chart="bars" viewBox="0 0 ${W} ${H}" role="img" aria-label="Systems ranked">${grid}${bars}</svg></div>`;
}

// ---------- Score against model size ----------
function sizeChart(points) {
  const pts = points.filter((p) => p.y != null && p.b > 0);
  if (pts.length < 3) return `<p class="small muted">Needs three systems with a known size.</p>`;
  const W = 760, H = 360, L = 52, R = 24, T = 16, B = 48;
  const lo = Math.log10(Math.min(...pts.map((p) => p.b)) / 1.5), hi = Math.log10(Math.max(...pts.map((p) => p.b)) * 1.5);
  const ys = pts.map((p) => p.y);
  const ymin = Math.max(0, Math.floor(Math.min(...ys) * 10 - 0.5) / 10), ymax = Math.min(1, Math.ceil(Math.max(...ys) * 10 + 0.3) / 10);
  const X = (b) => L + ((Math.log10(b) - lo) / (hi - lo)) * (W - L - R);
  const Y = (y) => T + (1 - (y - ymin) / (ymax - ymin)) * (H - T - B);
  const yt = []; for (let v = ymin; v <= ymax + 1e-9; v += 0.1) yt.push(+v.toFixed(1));
  const grid = yt.map((v) => `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" class="gridline"/><text x="${L - 8}" y="${Y(v) + 4}" text-anchor="end">${Math.round(v * 100)}</text>`).join("")
    + logTicks(lo, hi).map((v) => `<text x="${X(v)}" y="${H - B + 18}" text-anchor="middle">${v < 1 ? v * 1000 + "M" : v + "B"}</text>`).join("");
  // Label the best system of each size band, so the chart says which family wins at each size.
  const bands = new Map();
  for (const p of pts) { const k = Math.round(Math.log10(p.b) * 2); if (!bands.has(k) || bands.get(k).y < p.y) bands.set(k, p); }
  const named = [...bands.values()].sort((a, b) => b.y - a.y);
  const boxes = pts.map((p) => ({ x1: X(p.b) - 7, x2: X(p.b) + 7, y1: Y(p.y) - 7, y2: Y(p.y) + 7 }));
  const picks = placeLabels(named.map((p) => ({ cx: X(p.b), cy: Y(p.y), label: shortName(p.name) })), boxes, W, L);
  const lab = new Map(named.map((p, i) => [p, picks[i]]));
  const dots = pts.map((p) => {
    const at = lab.get(p);
    return `<g class="pt" data-sys="${esc(p.sys)}" tabindex="0" aria-label="${esc(p.name)}" ${tipAttr([p.name, `${typeLabel(p.type)} · ${p.params}`, `Overall ${pct(p.y)}`])}>
      <circle class="hit" cx="${X(p.b)}" cy="${Y(p.y)}" r="11"/>${marker(p.type, X(p.b), Y(p.y))}
      ${at ? `<text x="${at[0]}" y="${at[1]}" text-anchor="${at[2]}">${esc(shortName(p.name))}</text>` : ""}</g>`;
  }).join("");
  return `<div class="scroll plot"><svg class="chart" data-chart="size" viewBox="0 0 ${W} ${H}" role="img" aria-label="Overall score against model size">
    ${grid}<line x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}" class="axis"/>
    <text x="${(L + W - R) / 2}" y="${H - 8}" text-anchor="middle" class="label">Parameters (log scale). Mixture-of-experts models at their total size</text>
    <text x="14" y="${(T + H - B) / 2}" text-anchor="middle" class="label" transform="rotate(-90 14 ${(T + H - B) / 2})">Overall</text>
    ${dots}</svg></div>`;
}

// ---------- The chart section of the leaderboard ----------
// items: the leaderboard rows as filtered and viewed. Returns the HTML; wireCharts hooks up its controls.
function lbCharts(items) {
  const pts = items.map(({ r, s, p }) => ({
    sys: r.system, name: r.card?.name || r.system, type: modelType(r), params: r.card?.params || "", b: paramsB(r.card?.params),
    y: p?.scores.overall ?? null, cost: s.cost || {}, scores: p?.scores || {},
  }));
  const types = new Set(pts.map((p) => p.type));
  const shown = pts.filter((p) => !chS.hide.has(p.type));
  const xTabs = X_AXES.map(([k, l]) => `<button data-x="${k}" class="${chS.x === k ? "on" : ""}">${l}</button>`).join("");
  const bTabs = BAR_METRICS.map(([k, l]) => `<button data-bar="${k}" class="${chS.bar === k ? "on" : ""}">${l}</button>`).join("");
  const [, , barScore] = BAR_METRICS.find(([k]) => k === chS.bar) || BAR_METRICS[0];
  const barItems = shown.map((p) => ({ ...p, v: barScore ? p.scores[chS.bar] ?? null : p.cost[chS.bar] ?? null }));
  const head = (id, title, dir, extra = "") => `<div class="charthead" id="ch-${id}"><h2>${title}</h2>${higher(dir)}${extra}
    <button class="btn small" data-png="${id}" title="Save the chart as an image">PNG</button></div>`;
  return `
    ${head("value", "Score against cost", true, `<div class="tabs seg">${xTabs}</div>`)}
    <p class="lead">Each mark is one system. Up is a better Overall score, left is cheaper, faster or shorter. The shaded corner holds the systems above the median score and below the median ${chS.x === "eur_per_1000_pages" ? "cost" : chS.x === "seconds_per_page" ? "time" : "token count"} of those shown.</p>
    <div class="chartbar">${legend(types)}<label class="chk"><input type="checkbox" data-pareto ${chS.pareto ? "checked" : ""}> Best trade-off line</label></div>
    ${valueChart(shown.map((p) => ({ ...p, x: p.cost[chS.x] ?? null })), chS.x)}
    ${head("bars", "Ranked by one measure", barScore, `<div class="tabs seg">${bTabs}</div>`)}
    ${rankedBars(barItems, chS.bar, barScore)}
    ${head("size", "Score against model size", true)}
    <p class="lead">Size barely predicts the score here. The label marks the best system in each size band.</p>
    ${sizeChart(shown)}`;
}
function wireCharts(root, redraw) {
  root.querySelectorAll("[data-x]").forEach((b) => (b.onclick = () => { chSet("x", b.dataset.x); redraw(); }));
  root.querySelectorAll("[data-bar]").forEach((b) => (b.onclick = () => { chSet("bar", b.dataset.bar); redraw(); }));
  root.querySelectorAll("[data-hide]").forEach((b) => (b.onclick = () => {
    const h = new Set(chS.hide), k = b.dataset.hide;
    h.has(k) ? h.delete(k) : h.add(k);
    chSet("hide", h);
    redraw();
  }));
  const pr = root.querySelector("[data-pareto]");
  if (pr) pr.onchange = () => { chSet("pareto", pr.checked); redraw(); };
  const all = root.querySelector("[data-all]");
  if (all) all.onchange = () => { chSet("all", all.checked); redraw(); };
  wireTips(root);
}

// One tooltip for every chart: follows the pointer, and shows on keyboard focus too.
function wireTips(root) {
  let tip = document.getElementById("ctip");
  if (!tip) { tip = document.createElement("div"); tip.id = "ctip"; tip.setAttribute("role", "tooltip"); document.body.appendChild(tip); }
  const show = (el, x, y) => {
    const [first, ...rest] = el.dataset.tip.split("\n");
    tip.innerHTML = `<b>${esc(first)}</b>${rest.map((l) => `<div>${esc(l)}</div>`).join("")}`;
    tip.classList.add("show");
    const w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = `${Math.min(window.innerWidth - w - 8, x + 14)}px`;
    tip.style.top = `${Math.max(8, y - h - 10)}px`;
  };
  root.querySelectorAll("[data-tip]").forEach((el) => {
    el.onmousemove = (e) => show(el, e.clientX, e.clientY);
    el.onmouseleave = () => tip.classList.remove("show");
    el.onfocus = () => { const b = el.getBoundingClientRect(); show(el, b.right, b.top); };
    el.onblur = () => tip.classList.remove("show");
    el.onkeydown = (e) => { if (e.key === "Enter") el.dispatchEvent(new MouseEvent("click", { bubbles: true })); };
  });
}
