"""Blind second annotator: a second person labels a sample of pages without seeing the first label.

The two labels are scored against each other with the benchmark's own scorer. The result is the
agreement between two people, which is also the ceiling any system can be measured against.

A second label lives next to the first ones, in annotations/<document_id>/second/page-NNN.json.
When it is first saved as checked it keeps a copy of the first label as it was at that moment
(first_at_check). Agreement is always scored against that copy, so correcting the first label
afterwards cannot raise the figure. The copy is never overwritten and never sent to the page that
the second annotator works in.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

from . import gold, runner
from .compare import word_diff
from .corpus import Document, load_documents
from .metrics.markdown import split
from .metrics.page import score_page

STATUSES = ("marked", "draft", "checked")
SEED = 20261130


def _dir(doc: Document) -> Path:
    return gold._dir(doc) / "second"


def _path(doc: Document, page: int) -> Path:
    return _dir(doc) / f"page-{page:03d}.json"


def _has_text(rec: dict | None) -> bool:
    return bool(rec and str(rec.get("markdown", "")).strip())


def load(doc: Document, page: int) -> dict | None:
    p = _path(doc, page)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _write(doc: Document, page: int, rec: dict) -> None:
    p = _path(doc, page)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _status(rec: dict) -> str:
    """An empty draft is a pick, not a label (as for first labels)."""
    return "marked" if rec["status"] == "draft" and not _has_text(rec) else rec["status"]


def check_source(doc: Document, page: int, source: str | None) -> None:
    """A model that drafted the first label must not prefill the second one."""
    first = gold.load_page(doc, page) or {}
    if source and source.startswith("run:") and first.get("draft_source") == source:
        raise ValueError("That model drafted the first label. Pick another source so the two labels stay independent.")


def save(doc: Document, page: int, markdown: str, status: str, annotator: str = "", notes: str = "",
         draft_source: str | None = None) -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    if not 1 <= page <= doc.page_count:
        raise ValueError("page out of range")
    first = gold.load_page(doc, page)
    if not _has_text(first):
        raise ValueError("This page has no first label with text yet, so there is nothing to label a second time.")
    who = (annotator or "").strip()
    if who and who.casefold() == (first.get("annotator") or "").strip().casefold():
        raise ValueError("The second annotator must be a different person from the first. Use your own name.")
    if status == "checked" and not (markdown or "").strip():
        raise ValueError("A page with no text cannot be saved as checked.")
    check_source(doc, page, draft_source)
    old = load(doc, page) or {}
    at_check = old.get("first_at_check")
    if status == "checked" and not at_check:
        at_check = {"markdown": first["markdown"], "updated": first.get("updated", ""),
                    "annotator": first.get("annotator", "")}
    rec = {
        "document_id": doc.document_id, "page": page, "pdf_sha256": doc.sha256, "status": status,
        "annotator": who, "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "notes": notes,
        "draft_source": old.get("draft_source", "") if draft_source is None else draft_source,
        "markdown": markdown, "first_at_check": at_check,
    }
    _write(doc, page, rec)
    return rec


def public(rec: dict | None, page: int) -> dict:
    """What the second annotator's page may see: the record without the first label copy."""
    if not rec:
        return {"page": page, "status": "todo", "markdown": ""}
    return {k: v for k, v in rec.items() if k != "first_at_check"}


def pick(track: str, n: int, seed: int = SEED) -> list[tuple[str, int]]:
    """Choose n pages for the second annotator and write a marked record for each.

    Candidates are pages whose first label has text and that have no second record yet. The pick
    goes round the page kinds in turn, shuffled inside a kind with the seed, and takes no more than
    half of the pages from one document while another document can still supply one.
    """
    if n < 1:
        raise ValueError("Pick at least one page.")
    by_kind: dict[str, list[tuple[Document, int]]] = {}
    for doc in sorted(load_documents(track), key=lambda d: d.document_id):
        for page in range(1, doc.page_count + 1):
            first = gold.load_page(doc, page)
            if _has_text(first) and not _path(doc, page).exists():
                by_kind.setdefault(first.get("kind") or "unlabelled", []).append((doc, page))
    rng = random.Random(seed)
    for kind in sorted(by_kind):
        rng.shuffle(by_kind[kind])
    cap = max(1, n // 2)
    chosen: list[tuple[Document, int]] = []
    per_doc: dict[str, int] = {}
    for capped in (True, False):  # the second round fills what the cap left open
        progress = True
        while progress and len(chosen) < n:
            progress = False
            for kind in sorted(by_kind):
                if len(chosen) >= n:
                    break
                for i, (doc, page) in enumerate(by_kind[kind]):
                    if capped and per_doc.get(doc.document_id, 0) >= cap:
                        continue
                    chosen.append(by_kind[kind].pop(i))
                    per_doc[doc.document_id] = per_doc.get(doc.document_id, 0) + 1
                    progress = True
                    break
    out = []
    for doc, page in chosen:
        _write(doc, page, {"document_id": doc.document_id, "page": page, "pdf_sha256": doc.sha256, "status": "marked",
                           "annotator": "", "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                           "notes": "", "draft_source": "", "markdown": "", "first_at_check": None})
        out.append((doc.document_id, page))
    return out


def unpick(doc: Document, page: int) -> bool:
    """Remove a second record that holds no text. Returns whether one was removed."""
    rec = load(doc, page)
    if not rec:
        return False
    if _has_text(rec):
        raise ValueError("This second label holds text and is not removed.")
    _path(doc, page).unlink()
    return True


def _records(track: str):
    """Every second record of a track as (document id, page, record), in queue order."""
    root = gold.track_dir(track) / "annotations"
    for f in sorted(root.glob("*/second/page-*.json")) if root.exists() else []:
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
            yield f.parent.parent.name, int(rec["page"]), rec
        except (OSError, ValueError, KeyError, TypeError):
            continue


def queue(track: str) -> list[dict]:
    out = []
    for doc_id, page, rec in _records(track):
        first = {}
        try:
            first = json.loads((gold.track_dir(track) / "annotations" / doc_id / f"page-{page:03d}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        out.append({"document_id": doc_id, "page": page, "status": _status(rec), "kind": first.get("kind") or "unlabelled",
                    "lang": first.get("lang", ""), "annotator": rec.get("annotator", ""), "updated": rec.get("updated", "")})
    return sorted(out, key=lambda r: (r["document_id"], r["page"]))


def _scored(track: str):
    """(document, page, record, score) for every checked second label that kept a copy of the first."""
    docs = {d.document_id: d for d in load_documents(track)}
    for doc_id, page, rec in _records(track):
        doc, at = docs.get(doc_id), rec.get("first_at_check")
        if not doc or rec.get("status") != "checked" or not at or not _has_text(rec) or not _has_text(at):
            continue
        if rec.get("pdf_sha256") not in (None, doc.sha256):
            continue  # written for another revision of the PDF
        yield doc, page, rec, score_page(at["markdown"], rec["markdown"])


def agreement(track: str, detail: bool = False) -> dict | None:
    """How far two people agree, over checked second labels.

    The scorer treats the first label as the reference and the second as the prediction, so the
    figures are not symmetric in the last digits. The first label is the copy kept when the second
    one was checked, never the live one. None when no page qualifies.
    """
    rows = list(_scored(track))
    if not rows:
        return None
    items = [s for _, _, _, s in rows]
    out = {"pages": len(items), **runner._view(items),
           "publishable": track == "open" or len(items) >= runner.MIN_CLOSED_PAGES}
    if detail:
        out["per_page"] = [_per_page(doc, page, rec, s) for doc, page, rec, s in rows]
    return out


def _per_page(doc: Document, page: int, rec: dict, s: dict) -> dict:
    live = gold.load_page(doc, page) or {}
    n = s.get("numbers")
    return {"document_id": doc.document_id, "page": page, "kind": live.get("kind") or "unlabelled",
            "overall": runner._scores([s])["overall"], "text": s["text_score"],
            "tables": [t["teds"] for t in s["tables"]], "formulas": list(s["formulas"]),
            "numbers": n["matched"] / n["gold"] if n and n["gold"] else None}


def compare(doc: Document, page: int) -> dict:
    """Both labels of a page with the score and a word diff, once the second one is checked."""
    rec = load(doc, page)
    if not rec or rec.get("status") != "checked":
        raise PermissionError("The first label stays hidden until your second label is saved as checked.")
    at = rec.get("first_at_check")
    if not at:
        raise PermissionError("This second label has no copy of the first label. Save it as checked again.")
    live = gold.load_page(doc, page) or {}
    live_md = live.get("markdown", "")
    s = score_page(at["markdown"], rec["markdown"])
    return {
        "document_id": doc.document_id, "track": doc.track, "page": page, "page_count": doc.page_count,
        "first": {"markdown": at["markdown"], "updated": at.get("updated", ""), "annotator": at.get("annotator", "")},
        "second": {"markdown": rec["markdown"], "updated": rec.get("updated", ""), "annotator": rec.get("annotator", ""),
                   "draft_source": rec.get("draft_source", "")},
        "first_live": live_md if live_md != at["markdown"] else None,
        "score": {"overall": runner._scores([s])["overall"], "text": s["text_score"],
                  "tables": [t["teds"] for t in s["tables"]], "formulas": list(s["formulas"]),
                  "numbers": s["numbers"]},
        "diff": word_diff(split(at["markdown"])["text"], split(rec["markdown"])["text"]),
    }
