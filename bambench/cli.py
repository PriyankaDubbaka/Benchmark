"""Command line: python -m bambench <command>."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .paths import TRACKS


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bambench", description="BAM extraction benchmark (PW2)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("serve", help="start the local dashboard")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)

    s = sub.add_parser("list", help="list documents and systems")
    s.add_argument("--track", choices=TRACKS)

    s = sub.add_parser("add", help="register a PDF in a track")
    s.add_argument("pdf", type=Path)
    s.add_argument("--track", choices=TRACKS, default="closed")
    s.add_argument("--id", required=True, dest="document_id")
    s.add_argument("--title", default="")
    s.add_argument("--type", default="report", dest="doc_type")
    s.add_argument("--department", default="")
    s.add_argument("--family", default="", dest="family_id")
    s.add_argument("--language", default="en")
    s.add_argument("--split", default="dev", choices=("dev", "test"))
    s.add_argument("--year", type=int, help="year the document was issued")

    s = sub.add_parser("meta", help="change a document's title, year, department and so on")
    s.add_argument("document_id")
    s.add_argument("--track", choices=TRACKS, default="closed")
    s.add_argument("--year", type=int)
    s.add_argument("--department")
    s.add_argument("--family", dest="family_id")
    s.add_argument("--split", choices=("dev", "test"))
    s.add_argument("--type", dest="doc_type")
    s.add_argument("--language")
    s.add_argument("--title")
    s.add_argument("--rights", dest="rights_status")

    s = sub.add_parser("mark", help="pick pages of a document for annotation")
    s.add_argument("document_id")
    s.add_argument("pages", help="comma-separated page numbers, e.g. 1,4,7,18,28")
    s.add_argument("--track", choices=TRACKS, default="closed")
    s.add_argument("--unmark", action="store_true", help="drop the pick (pages with text are kept)")

    s = sub.add_parser("run", help="run a system on a track and score it")
    s.add_argument("system")
    s.add_argument("--track", choices=TRACKS, default="open")
    s.add_argument("--doc", action="append", dest="docs")
    s.add_argument("--draft-only", action="store_true",
                   help="predict every picked page as a prefill for annotation; score nothing")

    s = sub.add_parser("rescore", help="score saved outputs against the current gold, without running a model")
    s.add_argument("system", nargs="?", help="one system; leave out to rescore every system with a run")
    s.add_argument("--track", choices=TRACKS, default="open")

    s = sub.add_parser("export-site", help="write a read-only copy of the dashboard for static hosting")
    s.add_argument("out", type=Path, help="folder to write, e.g. public for GitLab Pages")

    sub.add_parser("leaderboard", help="print the leaderboard as JSON")
    sub.add_parser("export-closed", help="copy closed-track summaries with enough pages to results/closed")
    sub.add_parser("check-cards", help="check every system card against systems/schema/card.schema.json")
    sub.add_parser("guard", help="pre-commit check against committing closed-track files")

    a = ap.parse_args(argv)
    if a.cmd == "serve":
        from .server import serve
        serve(a.host, a.port)
    elif a.cmd == "list":
        from .corpus import load_documents
        from .server import _systems
        for t in [a.track] if a.track else TRACKS:
            for d in load_documents(t):
                print(f"{t:6} {d.document_id:28} {d.page_count:3} pages  {d.doc_type:11} {d.split}")
        for c in _systems():
            print(f"system {c['id']:26} {'ready' if c['available'] else 'unavailable: ' + c['reason']}")
    elif a.cmd == "add":
        from .corpus import register
        doc = register(a.track, a.pdf, a.document_id, copy_into_track=(a.track == "closed"), title=a.title,
                       doc_type=a.doc_type, department=a.department, family_id=a.family_id or a.document_id,
                       language=a.language, split=a.split, year=a.year,
                       rights_status="confidential" if a.track == "closed" else "unverified")
        print(f"added {doc.document_id} ({doc.page_count} pages) to the {a.track} track")
    elif a.cmd == "meta":
        from .corpus import get_document, update_meta
        names = ("year", "department", "family_id", "split", "doc_type", "language", "title", "rights_status")
        changes = {k: getattr(a, k) for k in names if getattr(a, k) is not None}
        if not changes:
            print("nothing to change: give at least one of --year, --department, --family, --split, --type, --language, --title, --rights")
            return 1
        try:
            before = get_document(a.track, a.document_id).to_json()
            after = update_meta(a.track, a.document_id, **changes).to_json()
        except (KeyError, ValueError) as e:
            print(e.args[0] if isinstance(e, KeyError) else e)
            return 1
        for k in changes:
            print(f"{a.document_id}: {k} {before.get(k, '—')!r} -> {after.get(k)!r}" if before.get(k) != after.get(k)
                  else f"{a.document_id}: {k} already {after.get(k)!r}")
    elif a.cmd == "mark":
        from .corpus import get_document
        from .gold import mark_pages
        pages = [int(x) for x in a.pages.replace(" ", "").split(",") if x]
        changed = mark_pages(get_document(a.track, a.document_id), pages, marked=not a.unmark)
        print(f"{'unmarked' if a.unmark else 'marked'} pages {changed or 'none (already set)'} of {a.document_id}")
    elif a.cmd == "run":
        from .runner import run
        res = run(a.system, a.track, a.docs, draft_only=a.draft_only)
        if res["summary"]:
            print(json.dumps(res["summary"]["scores"], indent=2))
    elif a.cmd == "rescore":
        from .runner import rescore, rescore_all
        if a.system:
            res = rescore(a.system, a.track)
            if not res:
                print(f"no saved run of {a.system} with annotated pages in the {a.track} track")
                return 1
            print(json.dumps(res["summary"]["scores"], indent=2))
        else:
            done = rescore_all(a.track)
            print(f"rescored {len(done)} systems" if done else f"no saved runs in the {a.track} track")
    elif a.cmd == "export-site":
        from .static_site import export
        n = export(a.out)
        print(f"wrote {n} files to {a.out}; closed-track rows only where 20 or more pages back them")
    elif a.cmd == "leaderboard":
        from .runner import leaderboard
        print(json.dumps(leaderboard(), indent=2))
    elif a.cmd == "export-closed":
        from .runner import export_closed
        done = export_closed()
        print("exported: " + (", ".join(done) if done else "nothing (no closed summary has enough pages yet)"))
    elif a.cmd == "check-cards":
        from .cards import check_all
        from .paths import SYSTEMS
        problems = check_all()
        for p in problems:
            print(p)
        if problems:
            return 1
        print(f"{len(list(SYSTEMS.glob('*.json')))} cards passed")
    elif a.cmd == "guard":
        from .guard import main as guard
        return guard()
    return 0


if __name__ == "__main__":
    sys.exit(main())
