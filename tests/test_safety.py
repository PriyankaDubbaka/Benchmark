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
