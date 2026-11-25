"""Leak check for a hosted copy of the dashboard.

Run it after `bambench export-site public` and before the folder is published. It fails when the
folder holds anything that has to stay inside BAM:

- any file export-site does not write: only the site's own files, config.js, the fixed api/*.json
  files and the open-track pair files may be there, so a PDF, page image, SVG or notes file fails
- a document id that is not in the open track, as a value or inside a list
- page text, page items or raw model outputs, which a hosted copy never carries
- a closed-track result that export-closed has not cleared: not published under results/closed with
  the same run, not publishable, or backed by fewer than 20 pages

Where the closed track is present on the machine (the BAM cluster or a VDI), it also decodes every
string in the JSON files and looks for every closed document id, title and PDF hash anywhere, and
for any line of closed label text or closed model output. Matching ignores Unicode form, JSON
escaping and runs of whitespace.

What it cannot do: in CI the closed track is absent, so free text under an unexpected key cannot be
recognised as closed there. Run it on the cluster or the VDI as well before committing results;
that is where the closed corpus is.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from .corpus import load_documents
from .gold import load_page, page_statuses
from .paths import SITE, published_dir, run_dir
from .runner import MIN_CLOSED_PAGES

# The JSON files export-site writes under api/, and the pair files it writes for the open track.
API_FILES = {"overview", "leaderboard", "models", "systems", "documents", "composition", "about"}
VERSUS = re.compile(r"api/versus/open/[^/]+/[^/]+\.json")
# Keys whose value names a document. A hosted copy only ever names open-track documents.
DOC_KEYS = {"document_id", "doc_id", "family_id"}
# Keys that hold page text or model output. None of them belongs in a hosted copy.
TEXT_KEYS = {"page_items", "markdown", "prediction", "predictions"}
MIN_LINE = 20  # closed lines shorter than this are too generic to search for


def _norm(s: str) -> str:
    return " ".join(unicodedata.normalize("NFC", s).split())


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path, k, v
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _decode(strings) -> tuple[list[str], set[str]]:
    """Each string normalised whole, and every line of every string normalised on its own."""
    whole, pieces = [], set()
    for s in strings:
        whole.append(_norm(s))
        pieces.update(n for line in s.splitlines() if len(n := _norm(line)) >= MIN_LINE)
    return whole, pieces


def _closed_needles() -> tuple[list[tuple[str, str]], set[str]]:
    """What must never appear in a hosted copy: (what, string) pairs searched as substrings, and a
    set of normalised lines of closed labels and outputs matched line by line. Empty without a
    closed track on this machine."""
    names, lines = [], set()
    docs = load_documents("closed")
    for d in docs:
        names += [("closed document id", d.document_id), ("closed PDF hash", d.sha256)]
        if d.title and len(d.title) >= 8:
            names.append(("closed document title", d.title))
        for p in page_statuses(d):
            for line in ((load_page(d, p) or {}).get("markdown") or "").splitlines():
                if len(n := _norm(line)) >= MIN_LINE:
                    lines.add(n)
    runs = run_dir("closed")
    for f in runs.rglob("page-*.md") if docs and runs.exists() else []:
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if len(n := _norm(line)) >= MIN_LINE:
                lines.add(n)
    return [(w, _norm(s)) for w, s in names if s], lines


def _cleared_closed() -> dict[str, str]:
    """system -> run_id of every closed summary export-closed has published."""
    out = {}
    for f in sorted(published_dir("closed").glob("*.json")) if published_dir("closed").exists() else []:
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        out[s.get("system", f.stem)] = s.get("run_id")
    return out


def _closed_result_problem(rel: str, path: str, res: dict, system, cleared: dict) -> str | None:
    pages = (res.get("counts") or {}).get("pages") or 0
    if not res.get("publishable") or pages < MIN_CLOSED_PAGES:
        return (f"{rel}: a closed-track result at {path or '/'} rests on {pages} pages or is not publishable; "
                f"only results cleared with {MIN_CLOSED_PAGES} or more pages may be published")
    if system not in cleared or (res.get("run_id") and cleared[system] and res["run_id"] != cleared[system]):
        return f"{rel}: the closed-track result of {system!r} at {path or '/'} was not cleared by export-closed"
    return None


def check(folder: Path) -> list[str]:
    """Problems found in an exported site folder. An empty list means it is safe to publish."""
    folder = Path(folder)
    if not (folder / "api").is_dir():
        return [f"{folder} has no api/ folder: run `bambench export-site {folder}` first"]
    problems = []
    open_docs = load_documents("open")
    open_ids, open_families = {d.document_id for d in open_docs}, {d.family_id for d in open_docs}
    site_files = {f.name for f in SITE.iterdir() if f.is_file()} | {"config.js"}
    cleared = _cleared_closed()
    decoded = {}  # rel -> (normalised strings, normalised lines), for the closed-corpus search
    for f in sorted(p for p in folder.rglob("*") if p.is_file()):
        rel = f.relative_to(folder).as_posix()
        is_api = rel.startswith("api/") and (rel[4:-5] in API_FILES and rel.endswith(".json") or VERSUS.fullmatch(rel))
        if not (is_api or ("/" not in rel and rel in site_files)):
            problems.append(f"{rel}: export-site never writes this file, so it has no place in a hosted copy")
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        if not rel.endswith(".json"):
            decoded[rel] = _decode([text])
            continue
        try:
            data = json.loads(text)
        except ValueError:
            problems.append(f"{rel}: not valid JSON")
            continue
        decoded[rel] = _decode(_strings(data))
        for path, k, v in _walk(data):
            if k in DOC_KEYS:
                allowed = open_families if k == "family_id" else open_ids
                for x in (v if isinstance(v, list) else [v]):
                    if not isinstance(x, str) or x not in allowed:
                        problems.append(f"{rel}: {k} {x!r} at {path or '/'} is not an open-track document")
            if k in TEXT_KEYS and v:
                problems.append(f"{rel}: {k!r} at {path or '/'} holds page text or model output")
        # Closed results: the closed column of a leaderboard row, and anything else marked as closed.
        if rel == "api/leaderboard.json" and isinstance(data, list):
            for i, row in enumerate(data):
                if isinstance(row, dict) and row.get("closed"):
                    res = row["closed"] if isinstance(row["closed"], dict) else {}
                    if (p := _closed_result_problem(rel, f"[{i}].closed", res, row.get("system"), cleared)):
                        problems.append(p)
        for path, k, v in _walk(data):
            if isinstance(v, dict) and v.get("track") == "closed" and ("scores" in v or "overall" in v) \
                    and not path.endswith("].closed") and k != "closed":
                if (p := _closed_result_problem(rel, f"{path}.{k}", v, v.get("system"), cleared)):
                    problems.append(p)
    names, lines = _closed_needles()
    if names or lines:
        for rel, (strings, pieces) in decoded.items():
            hit = next((what for what, s in names for x in strings if s in x), None)
            if not hit and not lines.isdisjoint(pieces):
                hit = "closed label or output text"
            if hit:
                problems.append(f"{rel}: contains {hit}")
    return problems
