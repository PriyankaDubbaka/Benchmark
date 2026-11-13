"""Score views, per-page items, paired comparison, composition, About and the new export files."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bambench import about as about_mod
from bambench import gold, pairs, runner
from bambench.composition import composition
from bambench.corpus import Document, get_document

VIEW_KEYS = {"pages", "overall", "e1_text", "e2_table_teds", "e2_table_teds_struct", "e3_formula",
             "numbers_recall", "numbers_precision", "ci95"}


def item(t, tb=(), f=(), n=None, o=False):
    return {"t": t, "tb": list(tb), "ts": list(tb), "f": list(f), "n": n, "o": o}


class Rooted(unittest.TestCase):
    """A temporary benchmark root: gold, runs, summaries and manifests live under self.tmp."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.doc = get_document("open", "bam-k009a")
        self.docs = [self.doc]
        for target, value in (
                ("bambench.gold.track_dir", lambda t: self.tmp / "gold"),
                ("bambench.corpus.track_dir", lambda t: self.tmp / "track" / t),
                ("bambench.runner.track_dir", lambda t: self.tmp / "track" / t),
                ("bambench.runner.run_dir", lambda t: self.tmp / "runs" / t),
                ("bambench.compare.run_dir", lambda t: self.tmp / "runs" / t),
                ("bambench.failures.run_dir", lambda t: self.tmp / "runs" / t),
                ("bambench.runner.summary_dir", lambda t: self.tmp / "summaries" / t),
                ("bambench.runner.published_dir", lambda t: self.tmp / "pub" / t / "summaries"),
                ("bambench.runner.load_documents", lambda t: self.docs),
                ("bambench.composition.load_documents", lambda t: self.docs),
                ("bambench.runner.MIN_CLOSED_PAGES", 1)):
            p = mock.patch(target, value)
            p.start()
            self.addCleanup(p.stop)

    def summary(self, track, system, items, **extra):
        d = self.tmp / "summaries" / track
        d.mkdir(parents=True, exist_ok=True)
        body = {"system": system, "track": track, "card": {}, "scores": {"overall": 0.5}, "counts": {"pages": 1},
                **({"page_items": items} if items is not None else {}), **extra}
        (d / f"{system}.json").write_text(json.dumps(body))

    def run_system(self, track="open"):
        return runner.run("pdftotext-rules", track, progress=lambda m: None)["summary"]


class Views(Rooted):
    def test_views_carry_interval_and_structure_score(self):
        for p in (1, 2):
            gold.save_page(self.doc, p, f"some text {p}\n\n<table><tr><td>a</td></tr></table>", "draft", kind="table", lang="en")
        s = self.run_system()
        self.assertIn("e2_table_teds_struct", s["scores"])
        for view in (s["by_kind"]["table"], s["by_lang"]["en"]):
            self.assertEqual(set(view), VIEW_KEYS)
            self.assertIsNotNone(view["ci95"])
        self.assertIn("e2_table_teds_struct", s["ci95"])

    def test_own_drafts_are_counted_and_flagged(self):
        gold.save_page(self.doc, 1, "text one", "draft")
        gold.save_page(self.doc, 2, "text two", "draft", draft_source="run:pdftotext-rules")
        s = self.run_system()
        self.assertEqual(s["counts"]["own_draft_pages"], 1)
        flags = {k: v["o"] for k, v in s["page_items"].items()}
        self.assertEqual(sorted(flags.values()), [False, True])
        scores = json.loads(next((self.tmp / "runs" / "open" / "pdftotext-rules").iterdir()).joinpath("scores.json").read_text())
        pages = scores["documents"][0]["pages"]
        self.assertEqual({p["own_draft"] for p in pages.values()}, {True, False})

    def test_excluding_own_drafts_none_some_all(self):
        gold.save_page(self.doc, 1, "text one", "draft")
        gold.save_page(self.doc, 2, "text two", "draft")
        self.assertIsNone(self.run_system()["excluding_own_drafts"])
        self.assertEqual(self.run_system()["counts"]["own_draft_pages"], 0)
        gold.save_page(self.doc, 2, "text two", "draft", draft_source="run:pdftotext-rules")
        some = runner.rescore("pdftotext-rules", "open", progress=lambda m: None)["summary"]
        self.assertEqual(some["excluding_own_drafts"]["pages"], 1)
        self.assertEqual(set(some["excluding_own_drafts"]), VIEW_KEYS)
        gold.save_page(self.doc, 1, "text one", "draft", draft_source="run:pdftotext-rules")
        every = runner.rescore("pdftotext-rules", "open", progress=lambda m: None)["summary"]
        self.assertEqual(every["excluding_own_drafts"]["pages"], 0)
        self.assertIsNone(every["excluding_own_drafts"]["overall"])
        self.assertIsNone(every["excluding_own_drafts"]["ci95"])

    def test_rescore_keeps_the_environment_of_the_run(self):
        gold.save_page(self.doc, 1, "text one", "draft")
        first = self.run_system()
        self.assertIn("packages", first["environment"])
        self.assertIn("weights_revision", first["environment"])
        self.assertIn("server", first["environment"])
        again = runner.rescore("pdftotext-rules", "open", progress=lambda m: None)["summary"]
        self.assertEqual(again["environment"], first["environment"])


class Failures(Rooted):
    def test_a_failed_run_is_remembered_and_a_good_run_forgets_it(self):
        from bambench import failures
        gold.save_page(self.doc, 1, "text one", "draft")
        with mock.patch("bambench.systems.pdftotext_rules.PdftotextRules.predict", side_effect=OSError("model server\n stopped")):
            with self.assertRaises(OSError):
                self.run_system()
        rec = failures.last("open", "pdftotext-rules")
        self.assertEqual(rec["error"], "model server stopped")
        self.run_system()
        self.assertIsNone(failures.last("open", "pdftotext-rules"))

    def test_an_empty_track_or_an_unknown_system_is_not_a_failure(self):
        from bambench import failures
        with self.assertRaises(runner.NothingToRun):
            self.run_system()
        self.assertIsNone(failures.last("open", "pdftotext-rules"))
        with self.assertRaises(KeyError):
            runner.run("no-such-system", "open")
        self.assertFalse((self.tmp / "runs" / "open" / "no-such-system").exists())


class ClosedStaysAggregate(Rooted):
    def test_closed_summary_and_export_hold_no_page_items_or_document_ids(self):
        gold.save_page(self.doc, 1, "text one", "draft", kind="prose", lang="en")
        gold.save_page(self.doc, 2, "text two", "draft")
        (self.tmp / "track" / "closed" / "documents").mkdir(parents=True)
        s = self.run_system("closed")
        self.assertNotIn("page_items", s)
        self.assertTrue(s["publishable"])
        self.assertEqual(runner.export_closed(), ["pdftotext-rules"])
        written = [f for f in (self.tmp / "pub").rglob("*") if f.is_file()]
        self.assertTrue(any(f.name == "progress.json" for f in written))
        text = "".join(f.read_text() for f in written)
        self.assertNotIn("page_items", text)
        self.assertNotIn(self.doc.document_id, text)
        progress = json.loads((self.tmp / "pub" / "closed" / "progress.json").read_text())
        self.assertNotIn("by_department", progress["composition"])
        self.assertNotIn("by_decade", progress["composition"])

    def test_leaderboard_drops_page_items_and_reads_old_summaries(self):
        self.summary("open", "new", {"d/1": item(0.5)}, scores={"overall": 0.5})
        old = {"system": "old", "track": "open", "card": {}, "scores": {"overall": 0.4}, "counts": {"pages": 2},
               "by_kind": {"prose": {"pages": 2, "overall": 0.4}}, "environment": {"python": "3"}}
        (self.tmp / "summaries" / "open" / "old.json").write_text(json.dumps(old))
        rows = {r["system"]: r for r in runner.leaderboard()}
        self.assertNotIn("page_items", rows["new"]["open"])
        self.assertEqual(rows["old"]["open"]["scores"]["overall"], 0.4)
        self.assertIn("cost", rows["old"]["open"])


class Versus(Rooted):
    def setUp(self):
        super().setUp()
        self.a = {f"d/{i}": item(0.9 - i * 0.05, tb=[0.8], f=[0.9], n=[10, 10, 9]) for i in range(1, 7)}
        self.b = {f"d/{i}": item(0.5 + i * 0.02, tb=[0.4], f=[0.5], n=[10, 10, 5]) for i in range(1, 7)}
        self.summary("open", "sa", self.a)
        self.summary("open", "sb", self.b)

    def test_difference_pages_won_and_publishable(self):
        r = pairs.versus("open", "sa", "sb")
        self.assertEqual((r["pages"], r["excluded_own_drafts"], r["paired"], r["publishable"]), (6, 0, True, True))
        m = r["metrics"]["overall"]
        self.assertAlmostEqual(m["diff"], m["a"] - m["b"])
        self.assertGreater(m["ci95"][0], 0)
        self.assertEqual(r["pages_won"], {"a": 6, "b": 0, "tie": 0})
        self.assertEqual(set(r["metrics"]), {"overall", "e1_text", "e2_table_teds", "e3_formula", "numbers_recall"})

    def test_swapping_sides_mirrors_the_result(self):
        r, s = pairs.versus("open", "sa", "sb"), pairs.versus("open", "sb", "sa")
        for k, m in r["metrics"].items():
            n = s["metrics"][k]
            self.assertEqual((m["a"], m["b"]), (n["b"], n["a"]))
            self.assertAlmostEqual(m["diff"], -n["diff"])
            self.assertEqual(m["ci95"], [-n["ci95"][1], -n["ci95"][0]])
        self.assertEqual(r["pages_won"]["a"], s["pages_won"]["b"])
        self.assertEqual(r["pages"], s["pages"])

    def test_pages_either_system_drafted_are_left_out_and_counted(self):
        self.a["d/1"]["o"] = True
        self.b["d/2"]["o"] = True
        self.summary("open", "sa", self.a)
        self.summary("open", "sb", self.b)
        r = pairs.versus("open", "sa", "sb")
        self.assertEqual((r["pages"], r["excluded_own_drafts"]), (4, 2))

    def test_only_common_pages_count_and_ties_are_called(self):
        b = {k: dict(v) for k, v in self.a.items() if k != "d/6"}
        b["d/1"] = item(0.9 - 0.05 + 0.001, tb=[0.8], f=[0.9], n=[10, 10, 9])
        self.summary("open", "sb", b)
        r = pairs.versus("open", "sa", "sb")
        self.assertEqual(r["pages"], 5)
        self.assertEqual(r["pages_won"], {"a": 0, "b": 0, "tie": 5})

    def test_missing_scores_and_no_common_page_raise_key_error(self):
        with self.assertRaisesRegex(KeyError, "no per-page scores"):
            pairs.versus("open", "sa", "nobody")
        self.summary("open", "sc", {"x/1": item(0.5)})
        with self.assertRaisesRegex(KeyError, "in common"):
            pairs.versus("open", "sa", "sc")
        with self.assertRaises(KeyError):
            pairs.versus("closed", "sa", "sb")  # nothing on disk for the closed track
        with self.assertRaises(KeyError):
            pairs.versus("open", "../sa", "sb")

    def test_summary_without_items_falls_back_to_the_saved_run(self):
        gold.save_page(self.doc, 1, "text one", "draft")
        gold.save_page(self.doc, 2, "text two", "draft")
        s = self.run_system()
        (self.tmp / "summaries" / "open" / "pdftotext-rules.json").write_text(
            json.dumps({k: v for k, v in s.items() if k != "page_items"}))
        self.assertEqual(pairs.page_items("open", "pdftotext-rules"), s["page_items"])

    def test_closed_pair_comes_from_scores_files_and_is_publishable_by_page_count(self):
        gold.save_page(self.doc, 1, "text one", "draft")
        gold.save_page(self.doc, 2, "text two", "draft")
        self.run_system("closed")
        run = next((self.tmp / "runs" / "closed" / "pdftotext-rules").iterdir())
        other = self.tmp / "runs" / "closed" / "other" / run.name
        other.mkdir(parents=True)
        shutil.copy(run / "scores.json", other / "scores.json")
        r = pairs.versus("closed", "other", "pdftotext-rules")
        self.assertEqual(r["pages"], 2)
        self.assertTrue(r["publishable"])
        with mock.patch("bambench.runner.MIN_CLOSED_PAGES", 20):
            self.assertFalse(pairs.versus("closed", "other", "pdftotext-rules")["publishable"])


class Composition(Rooted):
    def setUp(self):
        super().setUp()

        def doc(i, pages, **kw):
            return Document(document_id=f"doc-{i}", track="open", pdf="x.pdf", sha256="s", page_count=pages, **kw)

        self.docs = [doc(1, 3, family_id="f1", department="Dept A", extra={"year": 1994}),
                     doc(2, 2, family_id="f1", department="Dept B", language="de", split="test"),
                     doc(3, 1, family_id="f2", doc_type="report", rights_status="open")]
        d1, d2, d3 = self.docs
        gold.save_page(d1, 1, "a", "checked", kind="table", lang="en", draft_source="pdftotext")
        gold.save_page(d1, 2, "b", "draft", draft_source="run:x")
        gold.save_page(d1, 3, "", "draft")  # empty draft is a pick, not a label
        gold.save_page(d2, 1, "c", "draft")
        gold.save_page(d3, 1, "", "marked")
        second = self.tmp / "gold" / "annotations" / "doc-1" / "second"
        second.mkdir(parents=True)
        (second / "page-001.json").write_text(json.dumps({"markdown": "again"}))
        (second / "page-002.json").write_text(json.dumps({"markdown": "  "}))

    def test_counts(self):
        c = composition("open")
        self.assertEqual((c["documents"], c["pages"], c["labelled"], c["families"], c["second_labels"]), (3, 6, 3, 2, 1))
        self.assertEqual(c["by_status"], {"checked": 1, "draft": 2, "marked": 2})
        self.assertEqual(c["by_kind"], {"table": 1, "unlabelled": 2})
        self.assertEqual(c["by_lang"], {"en": 1, "unlabelled": 2})
        self.assertEqual(c["by_draft_source"], {"pdftotext": 1, "run:x": 1, "not recorded": 1})
        self.assertEqual(c["by_split"], {"dev": 2, "test": 1})
        self.assertEqual(c["by_decade"], {"1990s": 2, "not recorded": 1})
        self.assertEqual(c["by_department"], {"Dept A": 2, "Dept B": 1})
        self.assertEqual(c["by_doc_type"], {"certificate": {"documents": 2, "labelled": 3}, "report": {"documents": 1, "labelled": 0}})
        self.assertEqual(c["by_rights"]["open"], 1)

    def test_public_form_leaves_out_department_and_decade(self):
        c = composition("open", public=True)
        self.assertNotIn("by_department", c)
        self.assertNotIn("by_decade", c)
        self.assertEqual(c["labelled"], 3)


class About(unittest.TestCase):
    def test_real_citation_file(self):
        a = about_mod.about()
        self.assertEqual(a["version"], about_mod.__version__)
        self.assertTrue(a["citation"]["text"].startswith("Dubbaka, P. ("))
        self.assertIn("BAM Extraction Benchmark (PW2), version 0.1.0.", a["citation"]["text"])
        self.assertTrue(a["citation"]["text"].endswith("(BAM)."))
        self.assertIn("title:", a["citation"]["cff"])
        self.assertTrue(a["repository"].startswith("https://"))
        self.assertIn("Changelog", a["changelog"])

    def test_two_authors_contact_licence_and_date(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        (root / "CITATION.cff").write_text(
            'title: "Tiny Tool"\nabstract: >-\n  Folded text: with a colon\n  second line\nauthors:\n'
            '  - family-names: Alpha\n    given-names: Anna Maria\n  - family-names: Beta\n    given-names: Ben\n'
            'contact:\n  - email: "team@example.org"\nversion: 2.0.0\ndate-released: 2025-03-01\n'
            "repository-code: 'https://example.org/repo'\n")
        (root / "LICENSE").write_text("\nMIT Licence\nmore\n")
        with mock.patch("bambench.about.ROOT", root):
            a = about_mod.about()
        self.assertEqual(a["citation"]["text"], "Alpha, A. M. and Beta, B. (2025). Tiny Tool, version 2.0.0.")
        self.assertEqual((a["contact"], a["license"], a["repository"]), ("team@example.org", "MIT Licence", "https://example.org/repo"))
        self.assertEqual(a["changelog"], "")

    def test_missing_files_give_fallbacks(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        with mock.patch("bambench.about.ROOT", root):
            a = about_mod.about()
        self.assertEqual((a["license"], a["contact"], a["repository"], a["changelog"]), (None, None, None, ""))


class Export(Rooted):
    def test_export_writes_composition_about_and_open_pairs_only(self):
        from bambench import static_site
        for s in ("sb", "sa", "sc"):
            self.summary("open", s, {"bam-k009a/1": item(0.5 if s != "sa" else 0.7), "bam-k009a/2": item(0.4)})
        self.summary("open", "nopages", None)
        out = self.tmp / "public"
        static_site.export(out)
        api = out / "api"
        comp = json.loads((api / "composition.json").read_text())
        self.assertIsNone(comp["closed"])
        self.assertIn("by_department", comp["open"])
        self.assertIn("citation", json.loads((api / "about.json").read_text()))
        files = sorted(str(p.relative_to(api / "versus" / "open")) for p in (api / "versus" / "open").rglob("*.json"))
        self.assertEqual(files, ["sa/sb.json", "sa/sc.json", "sb/sc.json"])
        self.assertEqual(json.loads((api / "versus" / "open" / "sa" / "sb.json").read_text())["a"], "sa")
        self.assertFalse((api / "versus" / "closed").exists())
        self.assertNotIn("page_items", (api / "leaderboard.json").read_text())

    def test_published_closed_composition_is_passed_through(self):
        from bambench import static_site
        pub = self.tmp / "pub" / "closed"
        pub.mkdir(parents=True)
        (pub / "progress.json").write_text(json.dumps({"documents": 1, "pages": 2, "pages_checked": 0, "pages_draft": 0,
                                                       "composition": {"documents": 1, "labelled": 0}}))
        static_site.export(self.tmp / "public")
        comp = json.loads((self.tmp / "public" / "api" / "composition.json").read_text())
        self.assertEqual(comp["closed"], {"documents": 1, "labelled": 0})


if __name__ == "__main__":
    unittest.main()
