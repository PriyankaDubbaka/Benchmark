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
import random
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from . import __version__
from .corpus import load_documents, verify
from .cost import cost
from .gold import load_records, page_meta, pages_to_draft, scored_pages
from .metrics.page import score_page
from .metrics.records import ValidationError, score_records
from .paths import published_dir, run_dir, summary_dir, track_dir
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


BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_SEED = 20261130  # fixed, so the same pages always give the same interval


def _ci95(items: list[dict]) -> dict | None:
    """95% bootstrap interval for each score, resampling pages with replacement.

    It answers "how much would this number move with a different draw of pages like these".
    Pages of one report are not independent, so the true uncertainty is somewhat larger.
    """
    if len(items) < 2:
        return None
    rng = random.Random(BOOTSTRAP_SEED)
    keys = ("overall", "e1_text", "e2_table_teds", "e3_formula")
    draws: dict[str, list[float]] = {k: [] for k in keys}
    for _ in range(BOOTSTRAP_RESAMPLES):
        sc = _scores([items[rng.randrange(len(items))] for _ in items])
        for k in keys:
            if sc[k] is not None:
                draws[k].append(sc[k])
    out = {}
    for k, xs in draws.items():
        if len(xs) < 0.9 * BOOTSTRAP_RESAMPLES:
            continue  # too few pages carry this element for a stable interval
        xs.sort()
        out[k] = [round(xs[int(0.025 * len(xs))], 4), round(xs[min(len(xs) - 1, int(0.975 * len(xs)))], 4)]
    return out or None


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
        "documents": len(docs), "pages": n_pages, "runtime_s": round(elapsed, 1), "usage": system.usage,
    }, indent=2) + "\n", encoding="utf-8")
    if draft_only:
        progress(f"done: drafted {n_pages} pages in {len(docs)} documents, nothing scored")
        return {"summary": None, "run_id": run_id, "pages": n_pages}

    return _score(system_id, system.card, track, docs, predictions, run_id, out, elapsed, system.usage,
                  n_pages, progress)


def _score(system_id: str, card: dict, track: str, docs: list, predictions: dict, run_id: str, out, elapsed,
           usage, predicted_pages: int, progress=print, only_predicted: bool = False, keep: dict | None = None) -> dict:
    """Score saved predictions against the gold as it is now and write the summary.

    only_predicted is for rescoring an older run: a gold page the run never saw is left out and
    counted as missing, instead of being scored as an empty answer.
    """
    # Gold is loaded only from here on.
    per_doc, items, rec_f1 = [], [], []
    by_kind: dict[str, list] = {}
    not_own = []  # pages whose gold did not start as this system's own draft
    missing = 0   # gold pages an older run has no prediction for (rescore only)
    critical = {"wrong_unit": 0, "wrong_status": 0, "wrong_uncertainty": 0}
    for doc in docs:
        pred = predictions[doc.document_id]
        gold_pages = scored_pages(doc)
        drow = {"document_id": doc.document_id, "doc_type": doc.doc_type, "split": doc.split, "pages": {}}
        for p, gmd in gold_pages.items():
            if only_predicted and p not in pred["pages"]:
                missing += 1
                continue
            s = score_page(gmd, pred["pages"].get(p, ""))
            meta = page_meta(doc, p)
            s["kind"] = meta["kind"]
            drow["pages"][p] = s
            by_kind.setdefault(meta["kind"], []).append(s)
            if meta["draft_source"] != f"run:{system_id}":
                not_own.append(s)
            items.append(s)
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

    total = _scores(items)
    tables = [t for s in items for t in s["tables"]]
    keep = keep or {}
    summary = {
        "system": system_id,
        "track": track,
        "run_id": run_id,
        "bambench_version": __version__,
        "card": {k: v for k, v in card.items() if k not in ("page_prompt",)},
        "scores": {
            "overall": total["overall"],
            "e1_text": total["e1_text"],
            "e2_table_teds": total["e2_table_teds"],
            "e2_table_teds_struct": _avg([t["teds_struct"] for t in tables]),
            "e3_formula": total["e3_formula"],
            "e5_record_f1": _avg(rec_f1),
            "e5_critical_errors": critical if rec_f1 else None,
        },
        # How far each score could move with another draw of pages; see _ci95.
        "ci95": _ci95(items),
        "by_kind": {k: _scores(v) for k, v in sorted(by_kind.items())},
        # Same scores without the pages this system drafted, so its head start on them is visible.
        "excluding_own_drafts": _scores(not_own) if len(not_own) < len(items) else None,
        "counts": {"documents": len(docs), "pages": len(items), "predicted_pages": predicted_pages,
                   "tables": len(tables), "formulas": sum(len(s["formulas"]) for s in items),
                   "record_documents": len(rec_f1), "gold_pages_not_predicted": missing},
        "runtime_s": round(elapsed, 1) if elapsed is not None else None,
        "usage": usage,
        "environment": keep.get("environment") or
        {"python": platform.python_version(), "platform": platform.platform(), "gpu": _gpu()},
        "finished": keep.get("finished") or datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if keep:
        summary["rescored"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if track == "closed":
        summary["publishable"] = len(items) >= MIN_CLOSED_PAGES
    (out / "scores.json").write_text(json.dumps({"summary": summary, "documents": per_doc}, indent=2) + "\n",
                                     encoding="utf-8")
    sdir = summary_dir(track)
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / f"{system_id}.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    progress(f"done: overall={summary['scores']['overall']}")
    return {"summary": summary, "documents": per_doc}


def _saved_predictions(run: Path, docs: list) -> dict:
    """Read a finished run's page outputs back from disk, keyed like a fresh prediction."""
    out = {}
    for doc in docs:
        ddir = run / doc.document_id
        if not ddir.is_dir():
            continue
        pages = {}
        for f in sorted(ddir.glob("page-*.md")):
            try:
                pages[int(f.stem.split("-")[1])] = f.read_text(encoding="utf-8")
            except ValueError:
                continue
        rec = ddir / "records.json"
        out[doc.document_id] = {"pages": pages,
                                "records": json.loads(rec.read_text(encoding="utf-8")) if rec.exists() else None}
    return out


def rescore(system_id: str, track: str, progress=print) -> dict | None:
    """Score a system's newest saved outputs against the gold as it is now, without running the model.

    Use it after correcting or re-checking labels, or to add confidence intervals to an older run.
    Pages annotated after the run have no output to score: they are counted in
    counts.gold_pages_not_predicted, and the system needs a real rerun to cover them.
    """
    from .compare import runs_of
    from .systems import load_cards

    runs = runs_of(track, system_id)
    if not runs:
        return None
    run = runs[0]
    meta = json.loads((run / "run.json").read_text(encoding="utf-8")) if (run / "run.json").exists() else {}
    old = {}
    if (run / "scores.json").exists():
        old = json.loads((run / "scores.json").read_text(encoding="utf-8")).get("summary", {})
    card = old.get("card") or next((c for c in load_cards() if c["id"] == system_id), {"id": system_id})
    predictions = _saved_predictions(run, load_documents(track))
    docs = [d for d in load_documents(track) if d.document_id in predictions and scored_pages(d)]
    if not docs:
        return None
    predicted = sum(len(p["pages"]) for p in predictions.values())
    keep = {"environment": old.get("environment") or {"python": "", "platform": "", "gpu": "not recorded"},
            "finished": old.get("finished") or datetime.strptime(run.name, "%Y%m%dT%H%M%SZ").replace(
                tzinfo=timezone.utc).isoformat(timespec="seconds")}
    return _score(system_id, card, track, docs, predictions, run.name, run,
                  meta.get("runtime_s", old.get("runtime_s")), meta.get("usage", old.get("usage")),
                  meta.get("pages") or predicted, progress, only_predicted=True, keep=keep)


def rescore_all(track: str, progress=print) -> list[str]:
    d = run_dir(track)
    done = []
    for system_dir in sorted(p for p in d.iterdir() if p.is_dir()) if d.exists() else []:
        if rescore(system_dir.name, track, progress=lambda m: None):
            done.append(system_dir.name)
            progress(f"rescored {system_dir.name}")
    return done


def closed_progress() -> dict | None:
    """Counts of the closed track for the hosted site: numbers only, no document names."""
    from .gold import page_statuses

    if (track_dir("closed") / "documents").exists():
        docs = load_documents("closed")
        st = [s for d in docs for s in page_statuses(d).values()]
        return {"documents": len(docs), "pages": sum(d.page_count for d in docs),
                "pages_checked": st.count("checked"), "pages_draft": st.count("draft")}
    f = published_dir("closed").parent / "progress.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def export_closed() -> list[str]:
    """Copy closed-track summaries backed by enough pages into results/closed for publishing,
    together with the track's page counts. Nothing else about the closed track leaves its folder."""
    src, dst = summary_dir("closed"), published_dir("closed")
    done = []
    for f in sorted(src.glob("*.json")) if src.exists() else []:
        s = json.loads(f.read_text(encoding="utf-8"))
        if s.get("publishable"):
            dst.mkdir(parents=True, exist_ok=True)
            (dst / f.name).write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")
            done.append(s["system"])
    if (track_dir("closed") / "documents").exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        (dst.parent / "progress.json").write_text(json.dumps(closed_progress(), indent=2) + "\n", encoding="utf-8")
    return done


def leaderboard(published_only: bool = False) -> list[dict]:
    """One row per system with its open and closed summaries side by side.
    Closed rows come from the local closed folder when present, else from published results.
    published_only leaves the local closed folder out: that is what a hosted copy may show."""
    rows: dict[str, dict] = {}
    closed = [published_dir("closed")] if published_only else [published_dir("closed"), summary_dir("closed")]
    for track, dirs in (("open", [summary_dir("open")]), ("closed", closed)):
        files = {f.name: f for d in dirs if d.exists() for f in d.glob("*.json")}  # later dir wins
        for f in (files[k] for k in sorted(files)):
            s = json.loads(f.read_text(encoding="utf-8"))
            row = rows.setdefault(s["system"], {"system": s["system"], "card": s.get("card", {})})
            s["cost"] = cost(s)  # worked out on read, so older summaries get time and cost too
            row[track] = s
    return sorted(rows.values(), key=lambda r: -((r.get("open") or {}).get("scores", {}).get("overall") or -1))
