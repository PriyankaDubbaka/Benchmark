"""Score one page of predicted Markdown against its gold Markdown (tasks E1 to E3)."""
from __future__ import annotations

from .markdown import split
from .teds import teds
from .text import ned, normalize_formula, normalize_text


def _pairs(gold: list, pred: list, sim) -> list[tuple[float, int | None]]:
    """Greedy one-to-one matching by best similarity: (score, matched pred index) per gold item.
    Unmatched gold items score 0."""
    scored = sorted(((sim(g, p), gi, pi) for gi, g in enumerate(gold) for pi, p in enumerate(pred)), reverse=True)
    best: list[tuple[float, int | None]] = [(0.0, None)] * len(gold)
    used_g, used_p = set(), set()
    for s, gi, pi in scored:
        if gi in used_g or pi in used_p:
            continue
        best[gi] = (s, pi)
        used_g.add(gi)
        used_p.add(pi)
    return best


def score_page(gold_md: str, pred_md: str) -> dict:
    g, p = split(gold_md), split(pred_md)
    gt, pt = normalize_text(g["text"]), normalize_text(p["text"])
    tables = []
    for gi, (score, pi) in enumerate(_pairs(g["tables"], p["tables"], teds)):
        # TEDS-S on the same pairing as TEDS, so both numbers describe one predicted table.
        struct = teds(g["tables"][gi], p["tables"][pi], structure_only=True) if pi is not None else 0.0
        tables.append({"teds": score, "teds_struct": struct})
    formula_scores = [s for s, _ in _pairs(
        g["formulas"], p["formulas"], lambda a, b: 1 - ned(normalize_formula(a), normalize_formula(b))
    )]
    return {
        "text_score": 1 - ned(gt, pt),
        "text_chars": len(gt),
        "tables": tables,
        "pred_tables": len(p["tables"]),
        "formulas": formula_scores,
        "pred_formulas": len(p["formulas"]),
    }
