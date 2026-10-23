"""Side-by-side view of one page: the gold and every system's latest output, scored and diffed.

Reads only local run folders, so it works on the closed track without anything leaving BAM.
Scores are computed against the gold as it is now, so a corrected page shows corrected scores
without a rerun.
"""
from __future__ import annotations

import difflib
import json

from . import gold
from .corpus import Document
from .metrics.markdown import split
from .metrics.page import score_page
from .paths import run_dir
from .systems import load_cards

MAX_DIFF_TOKENS = 6000  # beyond this a word diff is too slow and too long to read


def runs_of(track: str, system_id: str) -> list:
    """Finished runs of a system, newest first. Draft-only runs have run.json but no scores."""
    d = run_dir(track) / system_id
    if not d.exists():
        return []
    return sorted((p for p in d.iterdir() if (p / "scores.json").exists() or (p / "run.json").exists()), reverse=True)


def latest_output(track: str, system_id: str, doc: Document, page: int) -> tuple[str, dict] | None:
    """The newest output of a system for this page, with facts about the run it came from."""
    for r in runs_of(track, system_id):
        f = r / doc.document_id / f"page-{page:03d}.md"
        if f.exists():
            meta = json.loads((r / "run.json").read_text(encoding="utf-8")) if (r / "run.json").exists() else {}
            return f.read_text(encoding="utf-8"), {"run_id": r.name, "draft_only": bool(meta.get("draft_only"))}
    return None


def word_diff(gold_text: str, pred_text: str) -> list[list[str]] | None:
    """Word-level diff as [op, text] runs: eq (both), del (in gold, missed), ins (model only)."""
    g, p = gold_text.split(), pred_text.split()
    if len(g) + len(p) > MAX_DIFF_TOKENS:
        return None
    out: list[list[str]] = []

    def add(op, words):
        if not words:
            return
        if out and out[-1][0] == op:
            out[-1][1] += " " + " ".join(words)
        else:
            out.append([op, " ".join(words)])

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, g, p, autojunk=False).get_opcodes():
        if tag == "equal":
            add("eq", p[j1:j2])
        else:
            add("del", g[i1:i2])
            add("ins", p[j1:j2])
    return out


def compare_page(doc: Document, page: int) -> dict:
    if not 1 <= page <= doc.page_count:
        raise ValueError(f"Page {page} out of range 1..{doc.page_count}")
    rec = gold.load_page(doc, page) or {}
    gold_md = rec.get("markdown", "") if rec.get("status") in ("draft", "checked") else ""
    gold_md = gold_md if gold_md.strip() else ""
    gold_text = split(gold_md)["text"] if gold_md else ""
    systems = []
    for card in load_cards():
        found = latest_output(doc.track, card["id"], doc, page)
        if not found:
            continue
        md, meta = found
        row = {"id": card["id"], "name": card.get("name", card["id"]), "markdown": md, **meta,
               "drafted_gold": rec.get("draft_source") == f"run:{card['id']}"}
        if gold_md:
            s = score_page(gold_md, md)
            row["score"] = {"text": s["text_score"], "tables": [t["teds"] for t in s["tables"]],
                            "formulas": s["formulas"]}
            row["diff"] = word_diff(gold_text, split(md)["text"])
        systems.append(row)
    systems.sort(key=lambda r: -(r.get("score", {}).get("text") or -1))
    return {
        "document_id": doc.document_id, "track": doc.track, "page": page, "page_count": doc.page_count,
        "gold": {"status": rec.get("status", "todo"), "markdown": gold_md, "kind": rec.get("kind", ""),
                 "lang": rec.get("lang", ""), "draft_source": rec.get("draft_source", "")},
        "systems": systems,
    }
