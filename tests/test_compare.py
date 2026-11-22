"""Side-by-side page view and the Models page."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bambench.compare import compare_page, word_diff
from bambench.corpus import Document


class WordDiff(unittest.TestCase):
    def test_marks_missing_and_extra_words(self):
        self.assertEqual(word_diff("Prüfung der Dichtung", "Prüfung Dichtung neu"),
                         [["eq", "Prüfung"], ["del", "der"], ["eq", "Dichtung"], ["ins", "neu"]])

    def test_gives_up_on_huge_pages(self):
        self.assertIsNone(word_diff("a " * 4000, "b " * 4000))


class ComparePage(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.doc = Document(document_id="r1", track="closed", pdf="x.pdf", sha256="a" * 64, page_count=3)
        for target in ("bambench.gold.track_dir", ):
            p = mock.patch(target, lambda t: self.tmp / "gold")
            p.start()
            self.addCleanup(p.stop)
        p = mock.patch("bambench.compare.run_dir", lambda t: self.tmp / "runs")
        p.start()
        self.addCleanup(p.stop)
        cards = [{"id": "a", "name": "Model A"}, {"id": "b", "name": "Model B"}, {"id": "c", "name": "Never ran"}]
        p = mock.patch("bambench.compare.load_cards", lambda: cards)
        p.start()
        self.addCleanup(p.stop)

    def _output(self, system, run_id, md, draft_only=False):
        d = self.tmp / "runs" / system / run_id / "r1"
        d.mkdir(parents=True)
        (d / "page-002.md").write_text(md, encoding="utf-8")
        (d.parent / "run.json").write_text(json.dumps({"draft_only": draft_only, "pages": 1, "runtime_s": 2}))

    def test_scores_every_system_against_current_gold(self):
        from bambench import gold
        gold.save_page(self.doc, 2, "Sealing of the closure plate", "draft", draft_source="run:b")
        self._output("a", "20261023T100000Z", "Sealing of the closure plate")
        self._output("b", "20261023T090000Z", "old")
        self._output("b", "20261023T110000Z", "Sealing closure plate", draft_only=True)
        c = compare_page(self.doc, 2)
        self.assertEqual([s["id"] for s in c["systems"]], ["a", "b"])  # best first, never-ran left out
        a, b = c["systems"]
        self.assertEqual(a["score"]["text"], 1.0)
        self.assertEqual(b["markdown"], "Sealing closure plate")  # newest run wins
        self.assertTrue(b["draft_only"] and b["drafted_gold"])
        self.assertIn(["del", "of the"], b["diff"])

    def test_page_without_gold_shows_outputs_unscored(self):
        self._output("a", "20261023T100000Z", "text")
        c = compare_page(self.doc, 2)
        self.assertEqual(c["gold"]["markdown"], "")
        self.assertNotIn("score", c["systems"][0])

    def test_page_out_of_range(self):
        with self.assertRaises(ValueError):
            compare_page(self.doc, 9)


class Catalog(unittest.TestCase):
    def test_lists_cards_claims_and_watchlist(self):
        from bambench.models import catalog, weights_downloaded
        systems = [{"id": "x", "model": "org/x", "handles": {"tables": True}, "available": True, "reason": ""}]
        board = [{"system": "x", "open": {"scores": {"overall": 0.8, "e1_text": 0.9, "e2_table_teds": 0.7, "e3_formula": None},
                                          "counts": {"pages": 5}, "by_kind": {"table": {"overall": 0.7}}}}]
        with mock.patch("bambench.models._speed", lambda t, s: None):
            m = catalog(systems, board)
        row = m["systems"][0]
        self.assertEqual(row["handles"]["tables"], True)
        self.assertIsNone(row["handles"]["handwriting"])
        self.assertEqual(row["results"]["open"]["by_kind"], {"table": 0.7})
        self.assertIsNone(row["results"]["closed"])
        self.assertTrue(any("EU" in w["reason"] for w in m["watchlist"]))
        self.assertIsNone(weights_downloaded(None))

    def test_detects_downloaded_weights(self):
        from bambench.models import weights_downloaded
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "hub/models--org--x/snapshots/abc").mkdir(parents=True)
            with mock.patch.dict("os.environ", {"HF_HOME": d}):
                self.assertTrue(weights_downloaded("org/x"))
                self.assertFalse(weights_downloaded("org/y"))
