"""Score one page of predicted Markdown against its gold Markdown (tasks E1 to E3)."""
from __future__ import annotations

from .markdown import split
from .teds import teds
from .text import ned, normalize_formula, normalize_text


def _match(gold: list, pred: list, sim) -> list[float]:
    """Greedy one-to-one matching by best similarity. Unmatched gold items score 0."""
    if not gold:
        return []
    pairs = sorted(((sim(g, p), gi, pi) for gi, g in enumerate(gold) for pi, p in enumerate(pred)), reverse=True)
    best = [0.0] * len(gold)
    used_g, used_p = set(), set()
    for s, gi, pi in pairs:
        if gi in used_g or pi in used_p:
            continue
        best[gi] = s
        used_g.add(gi)
        used_p.add(pi)
    return best


def score_page(gold_md: str, pred_md: str) -> dict:
    g, p = split(gold_md), split(pred_md)
    gt, pt = normalize_text(g["text"]), normalize_text(p["text"])
    table_scores = _match(g["tables"], p["tables"], teds)
    struct_scores = _match(g["tables"], p["tables"], lambda a, b: teds(a, b, structure_only=True))
    formula_scores = _match(
        g["formulas"], p["formulas"], lambda a, b: 1 - ned(normalize_formula(a), normalize_formula(b))
    )
    return {
        "text_score": 1 - ned(gt, pt),
        "text_chars": len(gt),
        "tables": [{"teds": t, "teds_struct": s} for t, s in zip(table_scores, struct_scores)],
        "pred_tables": len(p["tables"]),
        "formulas": formula_scores,
        "pred_formulas": len(p["formulas"]),
    }
