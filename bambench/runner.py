"""Run a system on a track, save its predictions, then score them.

Gold labels are read only after all predictions exist, as in the original starter.
Closed-track predictions and per-page scores stay in data/closed/runs (gitignored). Only an
aggregate summary is written to results/closed.

A draft-only run predicts every picked page, gold or not, and scores nothing. Its output is what
the dashboard offers as a prefill when a page is annotated.
"""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone
from statistics import mean

from . import __version__
from .corpus import load_documents, verify
from .gold import load_records, page_meta, pages_to_draft, scored_pages
from .metrics.page import score_page
from .metrics.records import ValidationError, score_records
from .paths import published_dir, run_dir, summary_dir
from .systems import get_system

MIN_CLOSED_PAGES = 20  # never publish a closed-track number backed by fewer pages


def _gpu() -> str:
    if not shutil.which("nvidia-smi"):
        return "none detected"
    try:
        return subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                              capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _avg(xs):
    return mean(xs) if xs else None


def _scores(items: list[dict]) -> dict:
    """E1, E2, E3 and overall over a set of scored pages."""
    e1 = _avg([s["text_score"] for s in items])
    e2 = _avg([t["teds"] for s in items for t in s["tables"]])
    e3 = _avg([f for s in items for f in s["formulas"]])
    parts = [x for x in (e1, e2, e3) if x is not None]
    return {"pages": len(items), "overall": mean(parts) if parts else None,
            "e1_text": e1, "e2_table_teds": e2, "e3_formula": e3}


def _pages_for(doc, draft_only: bool) -> list[int]:
    if draft_only:
        return pages_to_draft(doc)
    # Only annotated pages are scored; certificates with record gold are short and run whole.
    return list(range(1, doc.page_count + 1)) if load_records(doc) else sorted(scored_pages(doc))


def run(system_id: str, track: str, document_ids: list[str] | None = None, progress=print,
        draft_only: bool = False) -> dict:
    system = get_system(system_id)
    ok, why = system.available()
    if not ok:
        raise RuntimeError(f"{system_id} is not available: {why}")
    docs = [d for d in load_documents(track) if not document_ids or d.document_id in document_ids]
    docs = [d for d in docs if _pages_for(d, draft_only)]
    if not docs:
        raise RuntimeError(f"No {'picked' if draft_only else 'annotated'} pages in the {track} track yet")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = run_dir(track) / system_id / run_id
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()

    predictions = {}
    for i, doc in enumerate(docs, 1):
        verify(doc)
        pages = _pages_for(doc, draft_only)
        progress(f"[{i}/{len(docs)}] {doc.document_id}: {len(pages)} pages")
        pred = system.predict(doc, pages, lambda m, d=doc: progress(f"  {d.document_id} {m}"))
        predictions[doc.document_id] = pred
        ddir = out / doc.document_id
        ddir.mkdir(exist_ok=True)
        for p, md in pred["pages"].items():
            (ddir / f"page-{p:03d}.md").write_text(md, encoding="utf-8")
        if pred.get("records") is not None:
            (ddir / "records.json").write_text(json.dumps(pred["records"], indent=2) + "\n", encoding="utf-8")
    elapsed = time.time() - started
    n_pages = sum(len(p["pages"]) for p in predictions.values())
    (out / "run.json").write_text(json.dumps({
        "system": system_id, "track": track, "run_id": run_id, "draft_only": draft_only,
        "documents": len(docs), "pages": n_pages, "runtime_s": round(elapsed, 1),
    }, indent=2) + "\n", encoding="utf-8")
    if draft_only:
        progress(f"done: drafted {n_pages} pages in {len(docs)} documents, nothing scored")
        return {"summary": None, "run_id": run_id, "pages": n_pages}

    # Gold is loaded only from here on.
    per_doc, page_rows, tables, structs, formulas, rec_f1 = [], [], [], [], [], []
    by_kind: dict[str, list] = {}
    not_own = []  # pages whose gold did not start as this system's own draft
    critical = {"wrong_unit": 0, "wrong_status": 0, "wrong_uncertainty": 0}
    for doc in docs:
        pred = predictions[doc.document_id]
        gold_pages = scored_pages(doc)
        drow = {"document_id": doc.document_id, "doc_type": doc.doc_type, "split": doc.split, "pages": {}}
        for p, gmd in gold_pages.items():
            s = score_page(gmd, pred["pages"].get(p, ""))
            meta = page_meta(doc, p)
            s["kind"] = meta["kind"]
            drow["pages"][p] = s
            by_kind.setdefault(meta["kind"], []).append(s)
            if meta["draft_source"] != f"run:{system_id}":
                not_own.append(s)
            page_rows.append(s["text_score"])
            tables += [t["teds"] for t in s["tables"]]
            structs += [t["teds_struct"] for t in s["tables"]]
            formulas += s["formulas"]
        gold_rec = load_records(doc)
        if gold_rec and pred.get("records") is not None:
            try:
                r = score_records(gold_rec["records"], pred["records"], doc.page_count)
            except ValidationError as e:
                r = {"invalid": str(e), "record_f1": 0.0}
            drow["records"] = r
            rec_f1.append(r["record_f1"])
            for k in critical:
                critical[k] += r.get("critical_errors", {}).get(k, 0)
        per_doc.append(drow)

    e1, e2, e3 = _avg(page_rows), _avg(tables), _avg(formulas)
    parts = [x for x in (e1, e2, e3) if x is not None]
    summary = {
        "system": system_id,
        "track": track,
        "run_id": run_id,
        "bambench_version": __version__,
        "card": {k: v for k, v in system.card.items() if k not in ("page_prompt",)},
        "scores": {
            "overall": mean(parts) if parts else None,
            "e1_text": e1,
            "e2_table_teds": e2,
            "e2_table_teds_struct": _avg(structs),
            "e3_formula": e3,
            "e5_record_f1": _avg(rec_f1),
            "e5_critical_errors": critical if rec_f1 else None,
        },
        "by_kind": {k: _scores(v) for k, v in sorted(by_kind.items())},
        # Same scores without the pages this system drafted, so its head start on them is visible.
        "excluding_own_drafts": _scores(not_own) if len(not_own) < len(page_rows) else None,
        "counts": {"documents": len(docs), "pages": len(page_rows), "tables": len(tables),
                   "formulas": len(formulas), "record_documents": len(rec_f1)},
        "runtime_s": round(elapsed, 1),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "gpu": _gpu()},
        "finished": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if track == "closed":
        summary["publishable"] = len(page_rows) >= MIN_CLOSED_PAGES
    (out / "scores.json").write_text(json.dumps({"summary": summary, "documents": per_doc}, indent=2) + "\n",
                                     encoding="utf-8")
    sdir = summary_dir(track)
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / f"{system_id}.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    progress(f"done: overall={summary['scores']['overall']}")
    return {"summary": summary, "documents": per_doc}


def export_closed() -> list[str]:
    """Copy closed-track summaries backed by enough pages into results/closed for publishing."""
    src, dst = summary_dir("closed"), published_dir("closed")
    done = []
    for f in sorted(src.glob("*.json")) if src.exists() else []:
        s = json.loads(f.read_text(encoding="utf-8"))
        if s.get("publishable"):
            dst.mkdir(parents=True, exist_ok=True)
            (dst / f.name).write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")
            done.append(s["system"])
    return done


def leaderboard() -> list[dict]:
    """One row per system with its open and closed summaries side by side.
    Closed rows come from the local closed folder when present, else from published results."""
    rows: dict[str, dict] = {}
    for track, dirs in (("open", [summary_dir("open")]), ("closed", [published_dir("closed"), summary_dir("closed")])):
        files = {f.name: f for d in dirs if d.exists() for f in d.glob("*.json")}  # later dir wins
        for f in (files[k] for k in sorted(files)):
            s = json.loads(f.read_text(encoding="utf-8"))
            row = rows.setdefault(s["system"], {"system": s["system"], "card": s.get("card", {})})
            row[track] = s
    return sorted(rows.values(), key=lambda r: -((r.get("open") or {}).get("scores", {}).get("overall") or -1))
