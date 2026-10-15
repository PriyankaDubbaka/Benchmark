"""Closed-track guard rails and the local-only rule for model endpoints."""
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from bambench.guard import blocked
from bambench.systems.vllm_vlm import VllmVlm, allowed_host


class Guard(unittest.TestCase):
    def test_closed_files_are_blocked(self):
        self.assertEqual(blocked(["data/closed/pdfs/x.pdf", "data/closed/README.md", "bambench/cli.py"]),
                         ["data/closed/pdfs/x.pdf"])

    def test_gitignore_covers_closed_track(self):
        from bambench.paths import ROOT
        text = (ROOT / ".gitignore").read_text()
        self.assertIn("data/closed/*", text)


class LocalOnly(unittest.TestCase):
    def test_only_local_hosts_by_default(self):
        with mock.patch.dict(os.environ, {"BAMBENCH_ALLOWED_HOSTS": ""}):
            self.assertTrue(allowed_host("http://127.0.0.1:8000/v1"))
            self.assertTrue(allowed_host("http://localhost:8000/v1"))
            self.assertFalse(allowed_host("https://api.together.xyz/v1"))

    def test_named_bam_host_can_be_allowed(self):
        with mock.patch.dict(os.environ, {"BAMBENCH_ALLOWED_HOSTS": "gpu07.cluster.local"}):
            self.assertTrue(allowed_host("http://gpu07.cluster.local:8000/v1"))

    def test_refuses_to_send_pages_to_remote_host(self):
        s = VllmVlm({"id": "x", "kind": "vllm", "model": "m", "base_url": "https://api.example.com/v1"})
        self.assertFalse(s.available()[0])
        with self.assertRaises(PermissionError):
            s._chat("aGk=", "prompt")


class FakeVllm(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj):
        b = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._send({"data": [{"id": "fake/model"}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        prompt = body["messages"][0]["content"][1]["text"]
        if "JSON array" in prompt:
            content = '[{"element":"Al","value":0.587,"unit":"%","expanded_uncertainty":"0.018","coverage_factor":2,' \
                      '"status":"certified","oxide_formula":"Al2O3","oxide_value":"1.109"},{"element":"bad"}]'
        else:
            content = "```markdown\n# Title\n\n<table><tr><td>a</td></tr></table>\n```"
        self._send({"choices": [{"message": {"content": content}}]})


class VllmAdapter(unittest.TestCase):
    def test_round_trip_against_a_local_openai_compatible_server(self):
        srv = HTTPServer(("127.0.0.1", 0), FakeVllm)
        self.addCleanup(srv.server_close)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            from bambench.corpus import get_document
            card = {"id": "fake", "kind": "vllm", "model": "fake/model", "records": True,
                    "base_url": f"http://127.0.0.1:{srv.server_port}/v1", "dpi": 40}
            s = VllmVlm(card)
            self.assertEqual(s.available(), (True, ""))
            out = s.predict(get_document("open", "bam-s005c-v2"), [1], lambda m: None)
            self.assertTrue(out["pages"][1].startswith("# Title"))
            self.assertEqual([r["element"] for r in out["records"]], ["Al"])  # malformed row dropped
            self.assertEqual(out["records"][0]["value"], "0.587")
        finally:
            srv.shutdown()


if __name__ == "__main__":
    unittest.main()


class GuardGit(unittest.TestCase):
    def test_umlaut_paths_are_still_blocked(self):
        import subprocess
        import tempfile
        from pathlib import Path
        from bambench.guard import staged_files
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            f = Path(d) / "data/closed/Prüfbericht.pdf"
            f.parent.mkdir(parents=True)
            f.write_bytes(b"%PDF")
            subprocess.run(["git", "-C", d, "add", "-f", str(f)], check=True)
            cwd = os.getcwd()
            os.chdir(d)
            try:
                self.assertEqual(blocked(staged_files()), ["data/closed/Prüfbericht.pdf"])
            finally:
                os.chdir(cwd)


class GoldRules(unittest.TestCase):
    def _doc(self, split):
        import shutil
        import tempfile
        from pathlib import Path
        from bambench.corpus import Document
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        doc = Document(document_id="t", track="open", pdf="x.pdf", sha256="a" * 64, page_count=3, split=split)
        patcher = mock.patch("bambench.gold.track_dir", lambda t: Path(tmp))
        patcher.start()
        self.addCleanup(patcher.stop)
        return doc

    def test_drafts_do_not_count_on_test_split(self):
        from bambench import gold
        doc = self._doc("test")
        gold.save_page(doc, 1, "draft text", "draft")
        gold.save_page(doc, 2, "checked text", "checked")
        self.assertEqual(sorted(gold.scored_pages(doc)), [2])
        doc.split = "dev"
        self.assertEqual(sorted(gold.scored_pages(doc)), [1, 2])

    def test_labels_for_another_pdf_revision_are_ignored(self):
        from bambench import gold
        doc = self._doc("dev")
        gold.save_page(doc, 1, "text", "checked")
        doc.sha256 = "b" * 64
        self.assertEqual(gold.scored_pages(doc), {})


class PageImages(unittest.TestCase):
    def test_rendered_page_is_a_png_at_its_cache_path(self):
        from bambench.corpus import get_document, page_image
        p = page_image(get_document("open", "bam-k009a"), 1, 30)
        self.assertEqual(p.read_bytes()[:4], b"\x89PNG")
        self.assertEqual(p.name, "page-001-30.png")
