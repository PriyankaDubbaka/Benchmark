"""Page retrieval metrics (PW4 preview), ported from the starter scorer."""
from __future__ import annotations

import math

from .records import ValidationError, _check


def score_retrieval(queries: list, pred: list, page_count: int) -> dict:
    _check(isinstance(pred, list), "rankings must be an array")
    _check(len(queries) > 0, "Empty query reference")
    ids = {q["id"] for q in queries}
    _check(len(ids) == len(queries), "Duplicate reference queries")
    ranks = {}
    for r in pred:
        _check(isinstance(r, dict), "Bad ranking")
        _check(r.get("query_id") in ids, "Unknown query ID")
        _check(r["query_id"] not in ranks, "Duplicate query ID")
        pages = r.get("pages")
        _check(isinstance(pages, list) and all(isinstance(p, int) and 1 <= p <= page_count for p in pages),
               "Invalid page ranking")
        _check(len(set(pages)) == len(pages), "Duplicate ranked page")
        ranks[r["query_id"]] = pages
    per_query = []
    for q in queries:
        _check(len(q["evidence_pages"]) > 0, "Unanswerable queries need a separate protocol")
        pages = ranks.get(q["id"], [])
        rel = q["relevance"]
        relevant = [int(p) for p, g in rel.items() if g > 0]
        _check(relevant, "No positive relevance labels")
        o = {}
        for k in (1, 3, 5):
            top = pages[:k]
            o[f"recall_at_{k}"] = sum(p in relevant for p in top) / len(relevant)
            j = next((i for i, p in enumerate(top) if p in relevant), -1)
            o[f"mrr_at_{k}"] = 0.0 if j < 0 else 1 / (j + 1)
            dcg = sum((2 ** rel.get(str(p), 0) - 1) / math.log2(i + 2) for i, p in enumerate(top))
            ideal = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(sorted(rel.values(), reverse=True)[:k]))
            o[f"ndcg_at_{k}"] = dcg / ideal if ideal else 0.0
            o[f"complete_evidence_at_{k}"] = 1.0 if all(p in top for p in q["evidence_pages"]) else 0.0
        per_query.append({"id": q["id"], "category": q["category"], "ranking": pages, **o})
    keys = [k for k in per_query[0] if k not in ("id", "category", "ranking")]

    def means(rows):
        return {k: sum(r[k] for r in rows) / len(rows) for k in keys} if rows else {}

    cats = sorted({q["category"] for q in queries})
    return {
        "query_count": len(queries),
        "submitted_queries": len(ranks),
        "aggregate": means(per_query),
        "by_category": {c: means([r for r in per_query if r["category"] == c]) for c in cats},
        "per_query": per_query,
    }


__all__ = ["score_retrieval", "ValidationError"]
