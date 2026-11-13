"""Blind second annotator: storage, picking, agreement, the first-label copy, API and export."""
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

from bambench import gold, runner, second
from bambench.corpus import Document
from tests.test_views_and_pairs import Rooted

ONE = "Alpha beta gamma\n\n<table><tr><td>1</td><td>2</td></tr></table>"


def doc(track="open", document_id="doc-a", pages=6):
    return Document(document_id=document_id, track=track, pdf="x.pdf", sha256="0" * 64, page_count=pages)


class Base(Rooted):
    def setUp(self):
        super().setUp()
        self.a = doc()
        self.docs = [self.a]
        p = mock.patch("bambench.second.load_documents", lambda t: [d for d in self.docs if d.track == t])
        p.start()
        self.addCleanup(p.stop)
        self.label_first(self.a, 1, "Alpha beta gamma delta")

    def label_first(self, d, page, text, kind="prose", who="first-person"):
        gold.save_page(d, page, text, "draft", annotator=who, kind=kind, lang="en")


class Storage(Base):
    def test_needs_first_label_and_different_annotator(self):
        with self.assertRaises(ValueError):
            second.save(self.a, 2, "text", "draft", "second-person")  # page 2 has no first label
        with self.assertRaises(ValueError):
            second.save(self.a, 1, "text", "draft", " First-Person ")  # same name, any case
        with self.assertRaises(ValueError):
            second.save(self.a, 1, "", "checked", "second-person")
        with self.assertRaises(ValueError):
            second.save(self.a, 1, "x", "skip", "second-person")
        rec = second.save(self.a, 1, "Alpha beta", "draft", "second-person")
        self.assertIsNone(rec["first_at_check"])

    def test_first_at_check_is_taken_once_and_never_overwritten(self):
        second.save(self.a, 1, "Alpha beta gamma", "checked", "second-person")
        on_disk = json.loads(second._path(self.a, 1).read_text())
        self.assertEqual(on_disk["first_at_check"]["markdown"], "Alpha beta gamma delta")
        gold.save_page(self.a, 1, "Alpha beta gamma delta and more", "checked", annotator="first-person")
        second.save(self.a, 1, "Alpha beta gamma!", "checked", "second-person")
        again = json.loads(second._path(self.a, 1).read_text())
        self.assertEqual(again["first_at_check"]["markdown"], "Alpha beta gamma delta")
        self.assertNotIn("first_at_check", second.public(again, 1))

    def test_model_that_drafted_the_first_label_cannot_prefill_the_second(self):
        gold.save_page(self.a, 3, "some text", "draft", annotator="x", draft_source="run:m1")
        with self.assertRaises(ValueError) as cm:
            second.check_source(self.a, 3, "run:m1")
        self.assertIn("drafted the first label", str(cm.exception))
        second.check_source(self.a, 3, "run:m2")
        second.check_source(self.a, 3, "pdftotext")


class Picking(Base):
    def setUp(self):
        super().setUp()
        self.b = doc(document_id="doc-b", pages=6)
        self.docs = [self.a, self.b]
        for d in self.docs:
            for p in range(1, 7):
                self.label_first(d, p, f"text {d.document_id} {p}", kind=("prose", "table", "form")[p % 3])
        gold.save_page(self.b, 6, "", "marked")  # no text: never picked

    def test_pick_is_spread_deterministic_and_skips_picked_pages(self):
        got = second.pick("open", 6)
        self.assertEqual(len(got), 6)
        self.assertEqual({second._status(second.load(self.a if i == "doc-a" else self.b, p)) for i, p in got}, {"marked"})
        per_doc = [sum(1 for i, _ in got if i == d) for d in ("doc-a", "doc-b")]
        self.assertLessEqual(max(per_doc), 3)
        kinds = {gold.load_page(self.a if i == "doc-a" else self.b, p)["kind"] for i, p in got}
        self.assertEqual(kinds, {"prose", "table", "form"})
        self.assertNotIn(("doc-b", 6), got)
        more = second.pick("open", 3)
        self.assertFalse(set(more) & set(got))
        # the same state and seed give the same pick
        shutil.rmtree(self.tmp / "gold" / "annotations" / "doc-a" / "second")
        shutil.rmtree(self.tmp / "gold" / "annotations" / "doc-b" / "second")
        self.assertEqual(second.pick("open", 6), got)

    def test_one_document_may_exceed_half_when_there_is_no_choice(self):
        self.docs = [self.a]
        self.assertEqual(len(second.pick("open", 5)), 5)

    def test_unpick_removes_only_records_without_text(self):
        (d, p), = second.pick("open", 1)
        doc_ = self.a if d == "doc-a" else self.b
        second.save(doc_, p, "typed", "draft", "second-person")
        with self.assertRaises(ValueError):
            second.unpick(doc_, p)
        second.save(doc_, p, "", "draft", "second-person")
        self.assertTrue(second.unpick(doc_, p))
        self.assertFalse(second.unpick(doc_, p))

    def test_queue_lists_every_record(self):
        second.pick("open", 2)
        q = second.queue("open")
        self.assertEqual(len(q), 2)
        self.assertEqual(set(q[0]), {"document_id", "page", "status", "kind", "lang", "annotator", "updated"})


class Agreement(Base):
    def test_none_without_checked_pages_and_copy_decides_the_figure(self):
        self.assertIsNone(second.agreement("open"))
        second.save(self.a, 1, "Alpha beta gamma delta", "draft", "second-person")
        self.assertIsNone(second.agreement("open"))  # a draft does not count
        second.save(self.a, 1, "Alpha beta gamma delta", "checked", "second-person")
        a = second.agreement("open")
        self.assertEqual(a["pages"], 1)
        self.assertAlmostEqual(a["overall"], 1.0)
        self.assertIsNone(a["ci95"])
        self.assertTrue(a["publishable"])
        self.assertNotIn("per_page", a)
        # Making the live first label match the second one cannot move the figure.
        second.save(self.a, 1, "Alpha beta gamma", "checked", "second-person")
        before = second.agreement("open", detail=True)
        gold.save_page(self.a, 1, "Alpha beta gamma", "checked", annotator="first-person")
        after = second.agreement("open", detail=True)
        self.assertEqual(before["overall"], after["overall"])
        self.assertLess(after["overall"], 1.0)
        self.assertEqual(set(after["per_page"][0]), {"document_id", "page", "kind", "overall", "text", "tables", "formulas", "numbers"})

    def test_interval_appears_with_two_pages_and_closed_needs_enough_pages(self):
        self.label_first(self.a, 2, "One two three four")
        second.save(self.a, 1, "Alpha beta gamma delta", "checked", "s")
        second.save(self.a, 2, "One two three", "checked", "s")
        a = second.agreement("open")
        self.assertIsNotNone(a["ci95"])
        with mock.patch("bambench.runner.MIN_CLOSED_PAGES", 3):
            c = doc("closed", "conf-doc-77")
            self.docs.append(c)
            self.label_first(c, 1, "Secret words here")
            second.save(c, 1, "Secret words here", "checked", "s")
            self.assertFalse(second.agreement("closed")["publishable"])

    def test_compare_refuses_until_checked_and_reports_live_edit(self):
        second.save(self.a, 1, "Alpha beta", "draft", "second-person")
        with self.assertRaises(PermissionError):
            second.compare(self.a, 1)
        second.save(self.a, 1, "Alpha beta", "checked", "second-person")
        c = second.compare(self.a, 1)
        self.assertIsNone(c["first_live"])
        self.assertEqual(c["first"]["markdown"], "Alpha beta gamma delta")
        self.assertTrue(any(op == "del" for op, _ in c["diff"]))
        gold.save_page(self.a, 1, "Changed later", "checked", annotator="first-person")
        c = second.compare(self.a, 1)
        self.assertEqual(c["first_live"], "Changed later")
        self.assertEqual(c["first"]["markdown"], "Alpha beta gamma delta")


class Publishing(Base):
    def test_closed_export_and_site_hold_no_document_id(self):
        from bambench import static_site
        closed_id = "conf-report-4711"
        c = doc("closed", closed_id, pages=3)
        self.docs.append(c)
        (self.tmp / "track" / "closed" / "documents").mkdir(parents=True)
        self.label_first(c, 1, "Confidential prose here")
        self.label_first(c, 2, "More confidential words")
        second.save(c, 1, "Confidential prose here", "checked", "s")
        second.save(c, 2, "More confidential", "checked", "s")
        prog = runner.closed_progress()
        self.assertEqual(prog["agreement"]["pages"], 2)  # MIN_CLOSED_PAGES is patched to 1 here
        self.assertNotIn("per_page", prog["agreement"])
        runner.export_closed()
        out = self.tmp / "public"
        static_site.export(out)
        files = [f for d in (self.tmp / "pub", out) for f in d.rglob("*") if f.is_file()]
        self.assertTrue(files)
        for f in files:
            self.assertNotIn(closed_id.encode(), f.read_bytes(), f.name)
        ov = json.loads((out / "api" / "overview.json").read_text())
        self.assertEqual(ov["agreement"]["closed"]["pages"], 2)
        self.assertIsNone(ov["agreement"]["open"])

    def test_closed_agreement_is_not_published_below_the_minimum(self):
        c = doc("closed", "conf-report-4712", pages=2)
        self.docs.append(c)
        (self.tmp / "track" / "closed" / "documents").mkdir(parents=True)
        self.label_first(c, 1, "Confidential prose here")
        second.save(c, 1, "Confidential prose here", "checked", "s")
        with mock.patch("bambench.runner.MIN_CLOSED_PAGES", 5):
            self.assertIsNone(runner.closed_progress()["agreement"])


class Api(Base):
    """The real handler on a local port, over a document registered in the temporary root."""

    def setUp(self):
        super().setUp()
        from bambench import server
        for target, value in (("bambench.server.get_document", lambda t, i: next(d for d in self.docs if d.document_id == i)),
                              ("bambench.server.load_documents", lambda t: [d for d in self.docs if d.track == t]),
                              ("bambench.server.load_cards", lambda: [])):
            p = mock.patch(target, value)
            p.start()
            self.addCleanup(p.stop)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.httpd.local_only = True
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}/api/"

    def call(self, path, method="GET", body=None):
        req = urllib.request.Request(self.base + path, method=method, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def test_get_never_carries_the_copy_and_agree_is_refused_until_checked(self):
        base = "documents/open/doc-a/pages/1/"
        self.assertEqual(self.call(base + "second")[1], {"page": 1, "status": "todo", "markdown": ""})
        self.assertEqual(self.call(base + "agree")[0], 400)
        st, rec = self.call(base + "second", "PUT", {"markdown": "Alpha", "status": "checked", "annotator": "me"})
        self.assertEqual(st, 200)
        self.assertNotIn("first_at_check", rec)
        self.assertNotIn("first_at_check", self.call(base + "second")[1])
        self.assertIn("first_at_check", json.loads(second._path(self.a, 1).read_text()))
        st, c = self.call(base + "agree")
        self.assertEqual(st, 200)
        self.assertEqual(c["first"]["markdown"], "Alpha beta gamma delta")
        self.assertEqual(self.call(base + "second", "PUT", {"markdown": "x", "status": "draft", "annotator": "First-Person"})[0], 400)

    def test_queue_pick_unpick_and_overview(self):
        self.label_first(self.a, 2, "More words", kind="table")
        st, r = self.call("second/open/pick", "POST", {"n": 2})
        self.assertEqual((st, len(r["picked"]), len(r["queue"])), (200, 2, 2))
        st, r = self.call("second/open")
        self.assertEqual((len(r["queue"]), r["agreement"]), (2, None))
        d, p = r["queue"][0]["document_id"], r["queue"][0]["page"]
        self.assertTrue(self.call("second/open/unpick", "POST", {"document_id": d, "page": p})[1]["removed"])
        self.assertEqual(self.call("second/nowhere")[0], 404)

    def test_second_draft_route_refuses_the_first_labels_model(self):
        gold.save_page(self.a, 3, "some text", "draft", annotator="x", draft_source="run:m1")
        st, r = self.call("documents/open/doc-a/pages/3/second/draft?source=run:m1")
        self.assertEqual(st, 400)
        self.assertIn("Pick another source", r["error"])


if __name__ == "__main__":
    unittest.main()
