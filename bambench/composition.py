"""What the corpus is made of: counts of documents, pages and labels, never names or text.

Read from the document manifests and the label files, so it works for either track. The public
form of the closed track leaves out the department and decade splits, which could point at a
single report when a group is small.
"""
from __future__ import annotations

import json

from .corpus import load_documents
from .gold import _dir, load_page, page_statuses


def _bump(d: dict, key, n: int = 1) -> None:
    d[key] = d.get(key, 0) + n


def _decade(doc) -> str:
    y = doc.extra.get("year")
    return f"{y // 10 * 10}s" if isinstance(y, int) and not isinstance(y, bool) else "not recorded"


def _second_labels(doc) -> int:
    n = 0
    for f in (_dir(doc) / "second").glob("page-*.json"):
        try:
            n += bool(json.loads(f.read_text(encoding="utf-8")).get("markdown", "").strip())
        except (OSError, ValueError, AttributeError):
            continue
    return n


def composition(track: str, public: bool = False) -> dict:
    docs = load_documents(track)
    out = {"documents": len(docs), "pages": sum(d.page_count for d in docs), "labelled": 0, "second_labels": 0,
           "families": len({d.family_id for d in docs}),
           "by_status": {"checked": 0, "draft": 0, "marked": 0}, "by_kind": {}, "by_lang": {}, "by_doc_type": {},
           "by_draft_source": {}, "by_split": {}, "by_rights": {}, "by_department": {}, "by_decade": {}}
    for d in docs:
        out["second_labels"] += _second_labels(d)
        t = out["by_doc_type"].setdefault(d.doc_type, {"documents": 0, "labelled": 0})
        t["documents"] += 1
        _bump(out["by_rights"], d.rights_status)
        for p, st in page_statuses(d).items():
            if st in out["by_status"]:
                out["by_status"][st] += 1
            if st not in ("draft", "checked"):
                continue
            rec = load_page(d, p) or {}
            out["labelled"] += 1
            t["labelled"] += 1
            _bump(out["by_kind"], rec.get("kind") or "unlabelled")
            _bump(out["by_lang"], rec.get("lang") or "unlabelled")
            _bump(out["by_draft_source"], rec.get("draft_source") or "not recorded")
            _bump(out["by_split"], d.split)
            _bump(out["by_department"], d.department or "not recorded")
            _bump(out["by_decade"], _decade(d))
    if public:
        del out["by_department"], out["by_decade"]
    return out
