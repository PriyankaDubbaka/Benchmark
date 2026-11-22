"""Reference annotations.

Page gold is one JSON file per page holding Markdown: paragraphs as text, tables as HTML
<table> or pipe tables, display formulas as $$...$$. Page headers, footers and page numbers
are left out. Status is marked (picked for annotation, no text yet), draft (being written),
checked (reviewed again after a pause) or skip (looked at, not used). Only checked pages count on
a test split, and a page with no text never counts.

Each page can also carry its kind (cover, prose, table, ...), its language and the source its
first draft came from, so scores can be broken down by kind and a model is not credited for
pages whose gold started as its own output.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .corpus import Document
from .paths import track_dir

STATUSES = ("marked", "draft", "checked", "skip")
KINDS = ("cover", "prose", "table", "figure", "form", "formula", "mixed")
LANGS = ("en", "de", "en+de")


def _dir(doc: Document) -> Path:
    return track_dir(doc.track) / "annotations" / doc.document_id


def page_path(doc: Document, page: int) -> Path:
    return _dir(doc) / f"page-{page:03d}.json"


def load_page(doc: Document, page: int) -> dict | None:
    p = page_path(doc, page)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def save_page(doc: Document, page: int, markdown: str, status: str, annotator: str = "", notes: str = "",
              kind: str = "", lang: str = "", draft_source: str | None = None) -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    if not 1 <= page <= doc.page_count:
        raise ValueError("page out of range")
    if kind and kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    if lang and lang not in LANGS:
        raise ValueError(f"lang must be one of {LANGS}")
    old = load_page(doc, page) or {}
    rec = {
        "document_id": doc.document_id,
        "page": page,
        "pdf_sha256": doc.sha256,
        "status": status,
        "kind": kind,
        "lang": lang,
        # Where the first draft came from (pdftotext, run:<system>); kept unless a new prefill replaces it.
        "draft_source": old.get("draft_source", "") if draft_source is None else draft_source,
        "annotator": annotator,
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "notes": notes,
        "markdown": markdown,
    }
    p = page_path(doc, page)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return rec


def mark_pages(doc: Document, pages: list[int], marked: bool = True) -> list[int]:
    """Pick pages for annotation, or drop the pick. Pages that already hold text are never touched."""
    changed = []
    for page in pages:
        if not 1 <= page <= doc.page_count:
            raise ValueError(f"page {page} out of range 1..{doc.page_count}")
        rec = load_page(doc, page)
        has_text = bool(rec and rec.get("markdown", "").strip())
        if marked and not rec:
            save_page(doc, page, "", "marked")
            changed.append(page)
        elif not marked and rec and not has_text:
            page_path(doc, page).unlink()
            changed.append(page)
    return changed


def _status(rec: dict | None) -> str:
    if not rec:
        return "todo"
    if rec["status"] == "draft" and not rec.get("markdown", "").strip():
        return "marked"  # an empty draft is a pick, not a label
    return rec["status"]


def scored_pages(doc: Document, include_drafts: bool | None = None) -> dict[int, str]:
    """Pages with gold Markdown that count for scoring. Drafts count on dev only, unless told otherwise."""
    if include_drafts is None:
        include_drafts = doc.split != "test"
    out = {}
    for page in range(1, doc.page_count + 1):
        rec = load_page(doc, page)
        if _status(rec) in ("todo", "marked", "skip"):
            continue
        if rec.get("pdf_sha256") not in (None, doc.sha256):
            continue  # written for another revision of the PDF; never score it against this one
        if rec["status"] == "draft" and not include_drafts:
            continue
        out[page] = rec["markdown"]
    return out


def pages_to_draft(doc: Document) -> list[int]:
    """Every picked page, with or without text: what a draft-only run sends to a model."""
    return [p for p in range(1, doc.page_count + 1) if _status(load_page(doc, p)) not in ("todo", "skip")]


def page_meta(doc: Document, page: int) -> dict:
    rec = load_page(doc, page) or {}
    return {"kind": rec.get("kind") or "unlabelled", "lang": rec.get("lang", ""), "draft_source": rec.get("draft_source", "")}


def page_statuses(doc: Document) -> dict[int, str]:
    return {p: _status(load_page(doc, p)) for p in range(1, doc.page_count + 1)}


def load_records(doc: Document) -> dict | None:
    p = _dir(doc) / "records.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def load_queries(doc: Document) -> dict | None:
    p = _dir(doc) / "queries.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
