"""The Models page: every system card side by side with what it claims and what it scored here.

Claims come from the publisher (the `handles` block of a card). Scores come from our own runs.
A model on the watch list has no card yet; the list says why it is not in the benchmark.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .compare import runs_of
from .paths import SYSTEMS, TRACKS

CAPABILITIES = ("tables", "formulas", "handwriting", "german", "layout")
WATCHLIST = SYSTEMS / "watchlist" / "models.json"


def _hf_homes() -> list[Path]:
    homes = [os.environ.get("HF_HOME"), os.environ.get("BAMBENCH_MODELS")]
    return [Path(h) for h in homes if h] + [Path.home() / "models", Path.home() / ".cache" / "huggingface"]


def weights_downloaded(repo: str | None) -> bool | None:
    """True when the weights sit in a local Hugging Face cache; None for systems without weights."""
    if not repo or "/" not in repo:
        return None
    name = "models--" + repo.replace("/", "--")
    for home in _hf_homes():
        snaps = home / "hub" / name / "snapshots"
        if snaps.is_dir() and any(snaps.iterdir()):
            return True
    return False


def _speed(track: str, system_id: str) -> float | None:
    """Seconds per page from the newest run that recorded its runtime."""
    for r in runs_of(track, system_id):
        f = r / "run.json"
        if f.exists():
            meta = json.loads(f.read_text(encoding="utf-8"))
            if meta.get("pages"):
                return round(meta["runtime_s"] / meta["pages"], 2)
    return None


def _scores(summary: dict | None) -> dict | None:
    if not summary:
        return None
    by_kind = summary.get("by_kind") or {}
    return {
        "overall": summary["scores"]["overall"],
        "text": summary["scores"]["e1_text"],
        "tables": summary["scores"]["e2_table_teds"],
        "formulas": summary["scores"]["e3_formula"],
        "pages": summary["counts"]["pages"],
        "publishable": summary.get("publishable", True),
        "by_kind": {k: v["overall"] for k, v in by_kind.items()},
        "finished": summary.get("finished", ""),
    }


def catalog(systems: list[dict], leaderboard: list[dict]) -> dict:
    results = {row["system"]: row for row in leaderboard}
    rows = []
    for s in systems:
        res = results.get(s["id"], {})
        rows.append({
            **{k: v for k, v in s.items() if k not in ("serve",)},
            "serve": s.get("serve", ""),
            "handles": {c: s.get("handles", {}).get(c) for c in CAPABILITIES},
            "weights_downloaded": weights_downloaded(s.get("model")),
            "results": {t: _scores(res.get(t)) for t in TRACKS},
            "seconds_per_page": {t: _speed(t, s["id"]) for t in TRACKS},
        })
    watch = json.loads(WATCHLIST.read_text(encoding="utf-8")) if WATCHLIST.exists() else []
    return {"capabilities": list(CAPABILITIES), "systems": rows, "watchlist": watch}
