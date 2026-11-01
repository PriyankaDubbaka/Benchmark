"""Local dashboard: corpus, annotation, runs and leaderboard.

Standard library only, so it starts on a cluster login node or a laptop without installing
anything. It binds to 127.0.0.1 by default; reach it from your machine with an SSH tunnel
(ssh -L 8765:localhost:8765 <node>) rather than opening it to the network.
"""
from __future__ import annotations

import json
import mimetypes
import re
import tempfile
import threading
import traceback
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import __version__, gold, models, runner
from .compare import compare_page, latest_output, runs_of
from .corpus import get_document, load_documents, page_image, page_texts, register
from .paths import SITE, TRACKS
from .systems import KINDS, load_cards

JOBS: dict[str, dict] = {}
_LOCK = threading.Lock()
MAX_UPLOAD = 200 * 1024 * 1024


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _doc_summary(doc):
    statuses = gold.page_statuses(doc)
    return {
        **doc.to_json(),
        "track": doc.track,
        "pages_checked": sum(s == "checked" for s in statuses.values()),
        "pages_draft": sum(s == "draft" for s in statuses.values()),
        "pages_skipped": sum(s == "skip" for s in statuses.values()),
        "pages_marked": sum(s == "marked" for s in statuses.values()),
        "has_records": gold.load_records(doc) is not None,
        "page_status": statuses,
    }


def _systems():
    out = []
    for card in load_cards():
        cls = KINDS.get(card.get("kind"))
        ok, why = (cls(card).available() if cls else (False, "unknown kind"))
        out.append({**{k: v for k, v in card.items() if k != "page_prompt"}, "available": ok, "reason": why})
    return out


def _latest_run(track, system_id):
    scored = [p for p in runs_of(track, system_id) if (p / "scores.json").exists()]
    return scored[0] if scored else None


def _start_job(system_id, track, draft_only=False):
    job_id = uuid.uuid4().hex[:8]
    job = {"id": job_id, "system": system_id, "track": track, "draft_only": draft_only, "status": "running", "log": [],
           "started": _now(), "finished": None, "error": None}
    with _LOCK:  # check and insert under one lock so two clicks cannot start two runs
        if any(j["status"] == "running" for j in JOBS.values()):
            raise RuntimeError("A run is already in progress. Wait for it to finish.")
        JOBS[job_id] = job

    def log(msg):
        with _LOCK:
            job["log"].append(msg)
            del job["log"][:-200]

    def work():
        try:
            res = runner.run(system_id, track, progress=log, draft_only=draft_only)
            job["status"] = "done"
            job["overall"] = res["summary"]["scores"]["overall"] if res["summary"] else None
        except Exception as e:  # surfaced in the UI, full trace in the server console
            traceback.print_exc()
            job["status"] = "failed"
            job["error"] = str(e)
        job["finished"] = _now()

    threading.Thread(target=work, daemon=True).start()
    return job


class Handler(BaseHTTPRequestHandler):
    server_version = f"bambench/{__version__}"

    def log_message(self, fmt, *args):  # keep the console quiet apart from errors
        if args and str(args[1]).startswith(("4", "5")):
            super().log_message(fmt, *args)

    # helpers
    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, ctype=None):
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype or mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> bytes:
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_UPLOAD:
            raise ValueError("Upload too large")
        return self.rfile.read(n)

    def _route(self, method):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        parts = [unquote(p) for p in url.path.strip("/").split("/") if p]
        try:
            if not parts or parts[0] != "api":
                return self._static(url.path)
            return self._api(method, parts[1:], q)
        except KeyError as e:
            self._json({"error": str(e).strip("'")}, 404)
        except (ValueError, RuntimeError, PermissionError, FileNotFoundError) as e:
            self._json({"error": str(e)}, 400)
        except Exception as e:
            traceback.print_exc()
            self._json({"error": f"internal error: {e}"}, 500)

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def do_PUT(self):
        self._route("PUT")

    def _static(self, path):
        rel = path.lstrip("/") or "index.html"
        target = (SITE / rel).resolve()
        if not str(target).startswith(str(SITE.resolve())) or not target.is_file():
            target = SITE / "index.html"
        self._file(target)

    def _api(self, method, p, q):
        if p == ["overview"] and method == "GET":
            docs = [d for t in TRACKS for d in load_documents(t)]
            sums = [_doc_summary(d) for d in docs]
            by_track = {t: {"documents": sum(s["track"] == t for s in sums),
                            "pages": sum(s["page_count"] for s in sums if s["track"] == t),
                            "pages_checked": sum(s["pages_checked"] for s in sums if s["track"] == t),
                            "pages_draft": sum(s["pages_draft"] for s in sums if s["track"] == t)} for t in TRACKS}
            return self._json({"version": __version__, "tracks": by_track,
                               "systems": len(load_cards()), "leaderboard_rows": len(runner.leaderboard())})

        if p == ["documents"] and method == "GET":
            tracks = [q["track"]] if q.get("track") in TRACKS else list(TRACKS)
            return self._json([_doc_summary(d) for t in tracks for d in load_documents(t)])

        if p == ["documents"] and method == "POST":
            track = q.get("track", "closed")
            if track not in TRACKS:
                raise ValueError("track must be open or closed")
            data = self._body()
            if not data.startswith(b"%PDF"):
                raise ValueError("That file is not a PDF")
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(data)
            try:
                doc = register(track, Path(tmp.name), q.get("document_id", ""), copy_into_track=True,
                               title=q.get("title", ""), doc_type=q.get("doc_type", "report"),
                               department=q.get("department", ""), language=q.get("language", "en"),
                               family_id=q.get("family_id", "") or q.get("document_id", ""),
                               split=q.get("split", "dev"),
                               rights_status="confidential" if track == "closed" else "unverified")
            finally:
                Path(tmp.name).unlink(missing_ok=True)
            return self._json(_doc_summary(doc), 201)

        if len(p) >= 3 and p[0] == "documents":
            track, doc = p[1], get_document(p[1], p[2])
            if len(p) == 3:
                s = _doc_summary(doc)
                s["records"] = gold.load_records(doc)
                return self._json(s)
            if len(p) == 4 and p[3] == "mark" and method == "POST":
                b = json.loads(self._body() or b"{}")
                pages = [int(x) for x in b.get("pages", [])]
                changed = gold.mark_pages(doc, pages, bool(b.get("marked", True)))
                return self._json({"changed": changed, **_doc_summary(doc)})
            if len(p) >= 5 and p[3] == "pages":
                m = re.fullmatch(r"(\d+)(\.png)?", p[4])
                if not m:
                    raise KeyError("page")
                page = int(m.group(1))
                if m.group(2):
                    return self._file(page_image(doc, page, int(q.get("dpi", 110))), "image/png")
                if len(p) == 6 and p[5] == "annotation":
                    if method == "GET":
                        return self._json(gold.load_page(doc, page) or {"page": page, "status": "todo", "markdown": ""})
                    if method == "PUT":
                        b = json.loads(self._body() or b"{}")
                        return self._json(gold.save_page(doc, page, b.get("markdown", ""), b.get("status", "draft"),
                                                         b.get("annotator", ""), b.get("notes", ""),
                                                         b.get("kind", ""), b.get("lang", ""), b.get("draft_source")))
                if len(p) == 6 and p[5] == "draft" and method == "GET":
                    src = q.get("source", "pdftotext")
                    if src == "pdftotext":
                        text = page_texts(doc)[page - 1]
                        return self._json({"source": src, "draft_source": src, "markdown": "\n".join(
                            re.sub(r"\s{2,}", "  ", l).strip() for l in text.split("\n")).strip()})
                    if src.startswith("run:"):
                        # The newest run of that system that covers this page, scored or draft-only.
                        found = latest_output(track, src[4:], doc, page)
                        if not found:
                            raise KeyError(f"No run of {src[4:]} covers this page yet")
                        return self._json({"source": src, "draft_source": src, "run_id": found[1]["run_id"],
                                           "markdown": found[0]})
                    raise ValueError("unknown draft source")
            raise KeyError("Unknown document route")

        if p == ["systems"] and method == "GET":
            return self._json(_systems())

        if p == ["models"] and method == "GET":
            return self._json(models.catalog(_systems(), runner.leaderboard()))

        if len(p) == 4 and p[0] == "compare" and method == "GET":
            if not p[3].isdigit():
                raise KeyError("page")
            return self._json(compare_page(get_document(p[1], p[2]), int(p[3])))

        if p == ["leaderboard"] and method == "GET":
            return self._json(runner.leaderboard())

        if p == ["jobs"] and method == "GET":
            with _LOCK:
                return self._json(sorted(JOBS.values(), key=lambda j: j["started"], reverse=True))

        if p == ["jobs"] and method == "POST":
            b = json.loads(self._body() or b"{}")
            if b.get("track") not in TRACKS:
                raise ValueError("track must be open or closed")
            return self._json(_start_job(b["system"], b["track"], bool(b.get("draft_only"))), 202)

        if len(p) == 4 and p[0] == "runs" and p[3] == "latest" and method == "GET":
            latest = _latest_run(p[1], p[2])
            if not latest:
                raise KeyError("No runs yet")
            return self._json(json.loads((latest / "scores.json").read_text(encoding="utf-8")))

        raise KeyError("Unknown API route")


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    if host not in ("127.0.0.1", "localhost", "::1"):
        print(f"WARNING: listening on {host}. Anyone who can reach this port can read closed-track pages.")
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"BAM extraction benchmark dashboard on http://{host}:{port}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
