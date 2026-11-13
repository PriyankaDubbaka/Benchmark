"""Paired comparison of two systems on the pages both were scored on.

A difference between two leaderboard numbers can come from the pages each system happened to be
scored on. This compares them on the same pages only, leaves out pages either system drafted
(its own head start), and bootstraps the difference over pages so both are scored on the same
resample. Per-page items come from the open summary file, or from the newest scored run on disk,
which is the only source for the closed track. Nothing here carries a document name out.
"""
from __future__ import annotations

import json
import random
import re

from . import compare, runner

METRICS = ("overall", "e1_text", "e2_table_teds", "e3_formula", "numbers_recall")
TIE = 0.005  # two pages whose overall scores differ by less than this count as a tie


def _from_scores(track: str, system_id: str) -> dict | None:
    """Build page items from the documents list of the newest scored run."""
    for run in compare.runs_of(track, system_id):
        f = run / "scores.json"
        if not f.exists():
            continue
        out = {}
        for d in json.loads(f.read_text(encoding="utf-8")).get("documents", []):
            for page, s in (d.get("pages") or {}).items():
                n = s.get("numbers")
                out[f"{d['document_id']}/{page}"] = {
                    "t": s["text_score"], "tb": [t["teds"] for t in s["tables"]],
                    "ts": [t.get("teds_struct") for t in s["tables"]], "f": list(s["formulas"]),
                    "n": [n["gold"], n["pred"], n["matched"]] if n else None,
                    "o": bool(s.get("own_draft"))}
        return out or None
    return None


def page_items(track: str, system_id: str) -> dict | None:
    """Per-page scores of a system, keyed "<document_id>/<page>", or None when there are none."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", system_id):
        return None  # an id comes from a URL: never let it climb out of the run folders
    if track == "open":
        f = runner.summary_dir("open") / f"{system_id}.json"
        if f.exists():
            items = json.loads(f.read_text(encoding="utf-8")).get("page_items")
            if items:
                return items
    return _from_scores(track, system_id)


def _as_page(it: dict) -> dict:
    """A page item turned back into the dict shape runner._scores reads."""
    s = {"text_score": it["t"], "formulas": it["f"],
         "tables": [{"teds": a, "teds_struct": b} for a, b in zip(it["tb"], it.get("ts") or [None] * len(it["tb"]))]}
    if it.get("n"):
        s["numbers"] = dict(zip(("gold", "pred", "matched"), it["n"]))
    return s


def _interval(xs: list[float], draws: int) -> list[float] | None:
    if len(xs) < 0.9 * draws:
        return None  # too few resamples define this metric for both systems
    xs.sort()
    k = int(0.025 * len(xs))
    return [round(xs[k], 4), round(xs[len(xs) - 1 - k], 4)]  # symmetric, so swapping sides mirrors it


def versus(track: str, a: str, b: str) -> dict:
    if track not in ("open", "closed"):
        raise KeyError("track must be open or closed")
    ia, ib = page_items(track, a), page_items(track, b)
    for name, it in ((a, ia), (b, ib)):
        if not it:
            raise KeyError(f"{name} has no per-page scores on the {track} track yet")
    both = sorted(set(ia) & set(ib))
    if not both:
        raise KeyError(f"{a} and {b} were not scored on any page in common")
    keys = [k for k in both if not (ia[k].get("o") or ib[k].get("o"))]
    excluded = len(both) - len(keys)
    if not keys:
        raise KeyError(f"every page both were scored on was drafted by one of them ({excluded} pages)")
    pa = {k: _as_page(ia[k]) for k in keys}
    pb = {k: _as_page(ib[k]) for k in keys}

    sa, sb = runner._scores(list(pa.values())), runner._scores(list(pb.values()))
    rng = random.Random(runner.BOOTSTRAP_SEED)
    n = runner.BOOTSTRAP_RESAMPLES
    diffs: dict[str, list[float]] = {m: [] for m in METRICS}
    for _ in range(n):
        pick = [keys[rng.randrange(len(keys))] for _ in keys]  # one resample, both systems
        ra, rb = runner._scores([pa[k] for k in pick]), runner._scores([pb[k] for k in pick])
        for m in METRICS:
            if ra[m] is not None and rb[m] is not None:
                diffs[m].append(ra[m] - rb[m])

    won = {"a": 0, "b": 0, "tie": 0}
    for k in keys:
        x, y = runner._scores([pa[k]])["overall"], runner._scores([pb[k]])["overall"]
        if x is None or y is None or abs(x - y) < TIE:
            won["tie"] += 1
        else:
            won["a" if x > y else "b"] += 1
    metrics = {m: {"a": sa[m], "b": sb[m],
                   "diff": sa[m] - sb[m] if sa[m] is not None and sb[m] is not None else None,
                   "ci95": _interval(diffs[m], n)} for m in METRICS}
    return {"track": track, "a": a, "b": b, "pages": len(keys), "excluded_own_drafts": excluded, "paired": True,
            "publishable": track == "open" or len(keys) >= runner.MIN_CLOSED_PAGES,
            "metrics": metrics, "pages_won": won}
