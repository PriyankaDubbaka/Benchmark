"""Rescoring saved outputs, confidence intervals, the read-only site export and the request guard."""
import json
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from bambench import gold, runner
from bambench.corpus import get_document
from bambench.cost import cost


class Bootstrap(unittest.TestCase):
    def _page(self, text, tables=(), formulas=()):
        return {"text_score": text, "tables": [{"teds": t, "teds_struct": t} for t in tables], "formulas": list(formulas)}

    def test_interval_brackets_the_score_and_is_repeatable(self):
        items = [self._page(x, tables=[x]) for x in (0.2, 0.4, 0.5, 0.6, 0.9, 0.95)]
        ci = runner._ci95(items)
        point = runner._scores(items)["overall"]
        self.assertLess(ci["overall"][0], point)
        self.assertGreater(ci["overall"][1], point)
        self.assertEqual(ci, runner._ci95(items))  # fixed seed

    def test_identical_pages_give_a_zero_width_interval(self):
        ci = runner._ci95([self._page(0.5)] * 8)
        self.assertEqual(ci["e1_text"], [0.5, 0.5])
        self.assertNotIn("e2_table_teds", ci)  # no page has a table

    def test_one_page_has_no_interval(self):
        self.assertIsNone(runner._ci95([self._page(0.5)]))


class Rescore(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.doc = get_document("open", "bam-k009a")
        for target, value in (("bambench.gold.track_dir", lambda t: self.tmp / "gold"),
                              ("bambench.runner.run_dir", lambda t: self.tmp / "runs"),
                              ("bambench.compare.run_dir", lambda t: self.tmp / "runs"),
                              ("bambench.runner.summary_dir", lambda t: self.tmp / "summaries"),
                              ("bambench.runner.load_documents", lambda t: [self.doc])):
            p = mock.patch(target, value)
            p.start()
            self.addCleanup(p.stop)

    def test_corrected_gold_changes_the_score_without_a_rerun(self):
        gold.save_page(self.doc, 1, "wrong text entirely", "draft")
        first = runner.run("pdftotext-rules", "open", progress=lambda m: None)["summary"]
        run_id = first["run_id"]
        prediction = (self.tmp / "runs" / "pdftotext-rules" / run_id / "bam-k009a" / "page-001.md").read_text()
        gold.save_page(self.doc, 1, prediction, "draft")  # the label now matches what the system wrote
        again = runner.rescore("pdftotext-rules", "open", progress=lambda m: None)["summary"]
        self.assertGreater(again["scores"]["e1_text"], first["scores"]["e1_text"])
        self.assertEqual(again["run_id"], run_id)
        self.assertEqual(again["finished"], first["finished"])  # still says when the model ran
        self.assertIn("rescored", again)
        self.assertEqual(again["runtime_s"], first["runtime_s"])

    def test_pages_annotated_after_the_run_are_reported_not_scored_as_empty(self):
        gold.save_page(self.doc, 1, "some text", "draft")
        runner.run("pdftotext-rules", "open", progress=lambda m: None)
        run = next((self.tmp / "runs" / "pdftotext-rules").iterdir())
        (run / "bam-k009a" / "page-002.md").unlink(missing_ok=True)  # as if the run never saw page 2
        gold.save_page(self.doc, 2, "a page added later", "draft")
        s = runner.rescore("pdftotext-rules", "open", progress=lambda m: None)["summary"]
        self.assertEqual(s["counts"]["pages"], 1)
        self.assertEqual(s["counts"]["gold_pages_not_predicted"], 1)

    def test_no_saved_run_means_nothing_to_rescore(self):
        self.assertIsNone(runner.rescore("pdftotext-rules", "open"))


class CostUsesPagesRead(unittest.TestCase):
    def test_time_is_divided_by_every_page_the_model_read(self):
        s = {"runtime_s": 80.0, "card": {"slice": "20 GB"}, "counts": {"pages": 2, "predicted_pages": 8}}
        self.assertEqual(cost(s)["seconds_per_page"], 10.0)


class StaticSite(unittest.TestCase):
    def test_export_holds_no_closed_documents_and_only_published_closed_scores(self):
        from bambench import static_site
        out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out)
        local = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, local)
        (local / "secret-system.json").write_text(json.dumps({
            "system": "secret-system", "card": {}, "scores": {"overall": 0.5}, "counts": {"pages": 3},
            "publishable": False, "finished": "2026-11-01T00:00:00+00:00"}))
        with mock.patch("bambench.runner.summary_dir", lambda t: local if t == "closed" else local / "none"), \
                mock.patch("bambench.runner.published_dir", lambda t: local / "published" / t / "summaries"):
            static_site.export(out / "public")
        pub = out / "public"
        self.assertIn("BAMBENCH_STATIC = {", (pub / "config.js").read_text())
        board = json.loads((pub / "api" / "leaderboard.json").read_text())
        self.assertFalse(any(r["system"] == "secret-system" for r in board))
        docs = json.loads((pub / "api" / "documents.json").read_text())
        self.assertTrue(docs and all(d["track"] == "open" for d in docs))
        self.assertTrue((pub / "index.html").exists() and (pub / "app.js").exists())
        self.assertNotIn('"/', (pub / "index.html").read_text())  # relative links, so it works under a project path

    def test_export_refuses_to_write_into_the_source_folders(self):
        from bambench import static_site
        from bambench.paths import SITE
        with self.assertRaises(ValueError):
            static_site.export(SITE)


class RequestGuard(unittest.TestCase):
    def setUp(self):
        from bambench.server import Handler
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.srv.local_only = True
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.url = f"http://127.0.0.1:{self.srv.server_port}"

    def _status(self, path, headers=None, data=None, method="GET"):
        req = urllib.request.Request(self.url + path, headers=headers or {}, data=data, method=method)
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=5) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code

    def test_local_browser_is_served(self):
        self.assertEqual(self._status("/api/overview"), 200)
        self.assertEqual(self._status("/api/overview", {"Host": f"localhost:{self.srv.server_port}"}), 200)

    def test_rebound_hostname_cannot_read_the_api(self):
        self.assertEqual(self._status("/api/documents", {"Host": "attacker.example:8765"}), 403)

    def test_other_site_cannot_write(self):
        code = self._status("/api/jobs", {"Origin": "https://attacker.example", "Content-Type": "text/plain"},
                            data=b'{"system":"pdftotext-rules","track":"open"}', method="POST")
        self.assertEqual(code, 403)


if __name__ == "__main__":
    unittest.main()


class ScorerVersion(unittest.TestCase):
    def test_rows_from_an_older_scorer_are_marked(self):
        import tempfile
        from pathlib import Path
        from unittest import mock
        from bambench import runner
        from bambench.metrics import SCORER_VERSION
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            base = {"track": "open", "card": {}, "scores": {"overall": 0.5}, "counts": {"pages": 2},
                    "elapsed_seconds": 1.0}
            (d / "old.json").write_text(json.dumps({**base, "system": "old"}))
            (d / "new.json").write_text(json.dumps({**base, "system": "new", "scorer": SCORER_VERSION}))
            with mock.patch("bambench.runner.summary_dir", lambda t: d if t == "open" else d / "none"), \
                    mock.patch("bambench.runner.published_dir", lambda t: d / "none"):
                rows = {r["system"]: r["open"]["scorer_current"] for r in runner.leaderboard()}
        self.assertEqual(rows, {"old": False, "new": True})
