"""A read-only copy of the dashboard for static hosting, such as GitLab Pages.

The local dashboard needs its Python server because it annotates pages and starts runs. A hosted
copy only has to show results, so this writes the pages the frontend reads as plain JSON files next
to the site. It contains nothing from the closed track except what `bambench export-closed` has
already cleared for publishing: aggregate scores backed by enough pages, and page counts. No
document names, page text, images or raw outputs of closed reports are written.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, models, runner
from .corpus import load_documents
from .paths import ROOT, SITE
from .systems import load_cards


def _commit() -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _systems() -> list[dict]:
    # Nothing can be started from a hosted copy, so no system is "available" there.
    return [{**{k: v for k, v in c.items() if k != "page_prompt"}, "available": False,
             "reason": "read-only copy"} for c in load_cards()]


def export(out: Path) -> int:
    from .server import _doc_summary  # the same document rows the live dashboard shows

    out = Path(out)
    if out.resolve() in (ROOT.resolve(), SITE.resolve()):
        raise ValueError("choose a separate output folder, for example public")
    out.mkdir(parents=True, exist_ok=True)
    for f in SITE.iterdir():
        if f.is_file():
            shutil.copyfile(f, out / f.name)

    board = runner.leaderboard(published_only=True)
    open_docs = [_doc_summary(d) for d in load_documents("open")]
    closed = runner.closed_progress()  # None until `export-closed` has published the counts
    systems = _systems()
    catalog = models.catalog(systems, board)
    for s in catalog["systems"]:  # facts about one machine's disk and run folders mean nothing on a hosted copy
        s["weights_downloaded"] = None
        s["seconds_per_page"] = {t: (s["results"][t] and (next(r for r in board if r["system"] == s["id"])[t]
                                                         .get("cost", {}).get("seconds_per_page"))) or None
                                 for t in s["seconds_per_page"]}
    payload = {
        "overview": {
            "version": __version__,
            "tracks": {
                "open": {"documents": len(open_docs), "pages": sum(d["page_count"] for d in open_docs),
                         "pages_checked": sum(d["pages_checked"] for d in open_docs),
                         "pages_draft": sum(d["pages_draft"] for d in open_docs)},
                "closed": closed,
            },
            "systems": len(systems), "leaderboard_rows": len(board),
        },
        "leaderboard": board,
        "models": catalog,
        "systems": systems,
        "documents": open_docs,  # open track only: closed document names stay on BAM's cluster
    }
    api = out / "api"
    api.mkdir(exist_ok=True)
    for name, obj in payload.items():
        (api / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "config.js").write_text(
        "// Written by `bambench export-site`: this copy is read-only and loads its data from api/*.json.\n"
        f"window.BAMBENCH_STATIC = {json.dumps({'built': datetime.now(timezone.utc).isoformat(timespec='minutes'), 'commit': _commit(), 'version': __version__})};\n",
        encoding="utf-8")
    return sum(1 for f in out.rglob("*") if f.is_file())
