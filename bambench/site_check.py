"""Leak check for a hosted copy of the dashboard.

Run it after `bambench export-site public` and before the folder is published. It fails when the
folder holds anything that has to stay inside BAM:

- a file type the read-only site never needs, such as a PDF, a page image or an archive
- a document id that is not in the open track
- page text, page items or raw model outputs, which a hosted copy never carries
- a closed-track score that export-closed has not cleared (fewer than 20 pages, or not publishable)

Where the closed track is present on the machine (the BAM cluster or a VDI), it also searches the
folder for every closed document id, title and PDF hash, and for long lines of closed label text.
In CI the closed track is absent, so only the first four checks run there.
"""
from __future__ import annotations

import json
from pathlib import Path

from .corpus import load_documents
from .gold import load_page, page_statuses
from .runner import MIN_CLOSED_PAGES

ALLOWED_SUFFIXES = {".html", ".js", ".css", ".json", ".svg", ".ico", ".txt", ".md"}
# Keys whose value names a document. A hosted copy only ever names open-track documents.
DOC_KEYS = {"document_id", "doc_id", "family_id"}
# Keys that hold page text or model output. None of them belongs in a hosted copy.
TEXT_KEYS = {"page_items", "markdown", "prediction", "predictions"}
MIN_LINE = 40  # closed label lines shorter than this are too generic to search for


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path, k, v
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def _closed_needles() -> list[tuple[str, str]]:
    """Strings from the closed track that must never appear in a hosted copy. Empty without one."""
    needles = []
    for d in load_documents("closed"):
        needles += [("closed document id", d.document_id), ("closed PDF hash", d.sha256)]
        if d.title and len(d.title) >= 8:
            needles.append(("closed document title", d.title))
        for p in page_statuses(d):
            rec = load_page(d, p) or {}
            for line in (rec.get("markdown") or "").splitlines():
                line = line.strip()
                if len(line) >= MIN_LINE:
                    needles.append(("closed label text", line))
    return [(what, s) for what, s in needles if s]


def check(folder: Path) -> list[str]:
    """Problems found in an exported site folder. An empty list means it is safe to publish."""
    folder = Path(folder)
    if not (folder / "api").is_dir():
        return [f"{folder} has no api/ folder: run `bambench export-site {folder}` first"]
    problems = []
    open_ids = {d.document_id for d in load_documents("open")}
    open_families = {d.family_id for d in load_documents("open")}
    texts = {}
    for f in sorted(p for p in folder.rglob("*") if p.is_file()):
        rel = f.relative_to(folder).as_posix()
        if f.suffix.lower() not in ALLOWED_SUFFIXES:
            problems.append(f"{rel}: file type {f.suffix or '(none)'} has no place in a hosted copy")
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        texts[rel] = text
        if f.suffix != ".json":
            continue
        try:
            data = json.loads(text)
        except ValueError:
            problems.append(f"{rel}: not valid JSON")
            continue
        for path, k, v in _walk(data):
            if k in DOC_KEYS and isinstance(v, str) and v not in (open_families if k == "family_id" else open_ids):
                problems.append(f"{rel}: {k} {v!r} at {path or '/'} is not an open-track document")
            if k in TEXT_KEYS and v:
                problems.append(f"{rel}: {k!r} at {path or '/'} holds page text or model output")
            if k == "closed" and isinstance(v, dict) and "scores" in v:
                pages = (v.get("counts") or {}).get("pages", 0)
                if not v.get("publishable") or pages < MIN_CLOSED_PAGES:
                    problems.append(f"{rel}: a closed-track score at {path or '/'} rests on {pages} pages "
                                    f"or is not cleared; only {MIN_CLOSED_PAGES} or more cleared pages may be published")
    for what, needle in _closed_needles():
        for rel, text in texts.items():
            if needle in text or json.dumps(needle, ensure_ascii=False)[1:-1] in text:
                problems.append(f"{rel}: contains a {what}")
                break
    return problems
