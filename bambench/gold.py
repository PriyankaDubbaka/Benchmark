"""Reference annotations.

Page gold is one JSON file per page holding Markdown: paragraphs as text, tables as HTML
<table> or pipe tables, display formulas as $$...$$. Page headers, footers and page numbers
are left out. Status is draft (being written), checked (reviewed again after a pause) or skip
(page not selected for scoring). Only checked pages count on a test split.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .corpus import Document
from .paths import track_dir

STATUSES = ("draft", "checked", "skip")


def _dir(doc: Document) -> Path:
    return track_dir(doc.track) / "annotations" / doc.document_id


def page_path(doc: Document, page: int) -> Path:
    return _dir(doc) / f"page-{page:03d}.json"


def load_page(doc: Document, page: int) -> dict | None:
    p = page_path(doc, page)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def save_page(doc: Document, page: int, markdown: str, status: str, annotator: str = "", notes: str = "") -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    if not 1 <= page <= doc.page_count:
        raise ValueError("page out of range")
    rec = {
        "document_id": doc.document_id,
        "page": page,
        "pdf_sha256": doc.sha256,
        "status": status,
        "annotator": annotator,
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "notes": notes,
        "markdown": markdown,
    }
    p = page_path(doc, page)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return rec


def scored_pages(doc: Document, include_drafts: bool = True) -> dict[int, str]:
    """Pages with gold Markdown that count for scoring."""
    out = {}
    for page in range(1, doc.page_count + 1):
        rec = load_page(doc, page)
        if not rec or rec["status"] == "skip":
            continue
        if rec["status"] == "draft" and not include_drafts:
            continue
        out[page] = rec["markdown"]
    return out


def page_statuses(doc: Document) -> dict[int, str]:
    return {p: (load_page(doc, p) or {}).get("status", "todo") for p in range(1, doc.page_count + 1)}


def load_records(doc: Document) -> dict | None:
    p = _dir(doc) / "records.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def load_queries(doc: Document) -> dict | None:
    p = _dir(doc) / "queries.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
