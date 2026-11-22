"""Changing a document's descriptive fields, and the meta, add and check-cards commands."""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bambench import cli, corpus


class Meta(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.dir = self.tmp / "documents"
        self.dir.mkdir()
        self.f = self.dir / "doc-a.json"
        self.f.write_text(json.dumps({
            "document_id": "doc-a", "pdf": "x.pdf", "sha256": "ab" * 32, "page_count": 4, "title": "Old",
            "department": "D1", "split": "dev", "licence_url": "keep me"}))
        p = mock.patch("bambench.corpus.track_dir", lambda t: self.tmp)
        p.start()
        self.addCleanup(p.stop)

    def _read(self):
        return json.loads(self.f.read_text())

    def test_keeps_untouched_and_extra_fields_and_stores_year(self):
        doc = corpus.update_meta("closed", "doc-a", title="New", year=1998)
        raw = self._read()
        self.assertEqual((raw["title"], raw["year"], raw["department"]), ("New", 1998, "D1"))
        self.assertEqual(raw["licence_url"], "keep me")
        self.assertEqual((raw["sha256"], raw["pdf"], raw["page_count"]), ("ab" * 32, "x.pdf", 4))
        self.assertEqual(doc.extra["year"], 1998)
        corpus.update_meta("closed", "doc-a", split="test")  # year survives a later change
        self.assertEqual(self._read()["year"], 1998)

    def test_rejects_bad_keys_and_values_and_changes_nothing(self):
        before = self.f.read_text()
        for bad in ({"sha256": "x"}, {"pdf": "y.pdf"}, {"page_count": 9}, {"colour": "red"}, {"split": "train"},
                    {"year": 1800}, {"year": 2101}, {"year": "1999"}, {"year": True}, {"title": 5}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                corpus.update_meta("closed", "doc-a", **bad)
        with self.assertRaises(KeyError):
            corpus.update_meta("closed", "nope", title="x")
        self.assertEqual(self.f.read_text(), before)

    def _run(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(list(argv))
        return code, out.getvalue()

    def test_meta_command(self):
        code, out = self._run("meta", "doc-a", "--year", "2001", "--department", "D2", "--family", "fam",
                              "--split", "test", "--type", "report", "--language", "de", "--title", "T", "--rights", "ok")
        self.assertEqual(code, 0)
        self.assertIn("year", out)
        raw = self._read()
        self.assertEqual((raw["year"], raw["department"], raw["family_id"], raw["split"], raw["doc_type"],
                          raw["language"], raw["title"], raw["rights_status"]),
                         (2001, "D2", "fam", "test", "report", "de", "T", "ok"))
        self.assertEqual(raw["sha256"], "ab" * 32)

    def test_meta_command_errors_exit_one(self):
        self.assertEqual(self._run("meta", "doc-a")[0], 1)
        self.assertEqual(self._run("meta", "nope", "--year", "2000")[0], 1)
        self.assertEqual(self._run("meta", "doc-a", "--year", "1500")[0], 1)

    def test_add_takes_a_year(self):
        pdf = self.tmp / "in.pdf"
        pdf.write_bytes(b"%PDF")
        with mock.patch("bambench.corpus.pdf_page_count", lambda p: 2), mock.patch("bambench.corpus.ROOT", self.tmp):
            code, _ = self._run("add", str(pdf), "--track", "open", "--id", "doc-b", "--year", "1995")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((self.dir / "doc-b.json").read_text())["year"], 1995)

    def test_check_cards_command(self):
        code, out = self._run("check-cards")
        self.assertEqual(code, 0)
        self.assertIn("cards passed", out)
        with mock.patch("bambench.cards.check_all", lambda: ['x: unknown key "y"', "z: bad"]):
            code, out = self._run("check-cards")
        self.assertEqual((code, out.splitlines()), (1, ['x: unknown key "y"', "z: bad"]))


if __name__ == "__main__":
    unittest.main()
