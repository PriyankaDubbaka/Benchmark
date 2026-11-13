import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bambench import cards, failures, models
from bambench.paths import SYSTEMS
from bambench.systems import get_system
from bambench.systems.outputs import deepseek_grounding, front_matter
from bambench.systems.vllm_vlm import VllmVlm

SCHEMA = cards.load_schema()
GOOD = {"id": "qwen3.5-9b", "name": "Qwen", "kind": "vllm", "license": "MIT", "params": "9B"}


class Cards(unittest.TestCase):
    def test_every_card_passes_the_checks_and_loads(self):
        self.assertEqual(cards.check_all(), [])
        for f in sorted(SYSTEMS.glob("*.json")):
            with self.subTest(card=f.name):
                get_system(json.loads(f.read_text(encoding="utf-8"))["id"])

    def test_schema_file_is_not_loaded_as_a_card(self):
        self.assertFalse(list(SYSTEMS.glob("*schema*.json")))

    def test_misspelt_key_is_caught_with_a_suggestion(self):
        p = cards.validate({**GOOD, "licence": "MIT"}, SCHEMA)
        self.assertEqual(p, ['qwen3.5-9b: unknown key "licence" (did you mean "license"?)'])

    def test_missing_required_key(self):
        c = {k: v for k, v in GOOD.items() if k != "params"}
        self.assertEqual(cards.validate(c, SCHEMA), ['qwen3.5-9b: missing required key "params"'])

    def test_wrong_enum_value(self):
        p = cards.validate({**GOOD, "status": "done"}, SCHEMA)
        self.assertEqual(len(p), 1)
        self.assertIn('status is "done", expected one of pending, active', p[0])

    def test_bad_released_slice_and_handles(self):
        for key, bad in (("released", "March 2026"), ("slice", "big"), ("source", "http://x.org"),
                         ("revision", "xyz"), ("weights_gb", "7")):
            with self.subTest(key=key):
                self.assertEqual(len(cards.validate({**GOOD, key: bad}, SCHEMA)), 1)
        self.assertEqual(len(cards.validate({**GOOD, "handles": {"tables": "yes"}}, SCHEMA)), 1)
        self.assertEqual(len(cards.validate({**GOOD, "handles": {"table": True}}, SCHEMA)), 1)
        ok = {**GOOD, "released": "2026-03", "slice": "40 GB", "handles": {"tables": None, "layout": True}}
        self.assertEqual(cards.validate(ok, SCHEMA), [])

    def _with_card(self, **extra):
        """check_all on a copy of the cards folder with one more card."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        shutil.copytree(SYSTEMS, tmp / "systems")
        (tmp / "systems" / "extra.json").write_text(json.dumps({**GOOD, "id": "extra", **extra}))
        with mock.patch("bambench.cards.SYSTEMS", tmp / "systems"):
            return cards.check_all()

    def test_superseded_by_must_name_a_card(self):
        p = self._with_card(status="superseded", superseded_by="nothing-here")
        self.assertEqual(p, ['extra: superseded_by names "nothing-here", which is not a card'])

    def test_superseded_by_and_status_go_together(self):
        self.assertIn("extra: status is superseded but superseded_by is not set", self._with_card(status="superseded"))
        self.assertIn("extra: superseded_by is set but status is not superseded",
                      self._with_card(superseded_by="qwen3.5-9b"))
        self.assertEqual(self._with_card(status="superseded", superseded_by="qwen3.5-9b"), [])

    def test_cross_rules(self):
        self.assertIn('extra: unknown kind "magic", expected one of', self._with_card(kind="magic")[0])
        self.assertTrue(any("no \"model\"" in x for x in self._with_card(serve="vllm serve m")))
        self.assertTrue(any("must start with vllm" in x for x in self._with_card(model="m", serve="python x")))
        self.assertTrue(any("--port" in x for x in self._with_card(model="m", serve="vllm serve m --port 1")))
        self.assertTrue(any("unknown output converter" in x for x in self._with_card(output="nope")))

    def test_status_rule(self):
        fail = {"when": "2026-01-01T00:00:00+00:00", "error": "boom"}
        self.assertEqual(cards.status_of({}, True, None), ("active", ""))
        self.assertEqual(cards.status_of({}, True, fail), ("active", ""))  # a result outranks an old failure
        self.assertEqual(cards.status_of({"status_note": "n"}, False, None), ("pending", "n"))
        self.assertEqual(cards.status_of({"status_note": "n"}, False, fail), ("failed", "boom"))
        for st in ("superseded", "withdrawn", "failed"):
            self.assertEqual(cards.status_of({"status": st, "status_note": "n"}, True, None), (st, "n"))
        self.assertEqual(cards.status_of({"status": "active"}, False, None), ("pending", ""))


class Failures(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        p = mock.patch("bambench.failures.run_dir", lambda t: self.tmp / t / "runs")
        p.start()
        self.addCleanup(p.stop)

    def test_record_last_clear(self):
        self.assertIsNone(failures.last("open", "x"))  # folder does not exist yet
        failures.record("open", "x", "line one\nline two " + "a" * 400)
        rec = failures.last("open", "x")
        self.assertEqual(set(rec), {"when", "error"})
        self.assertNotIn("\n", rec["error"])
        self.assertEqual(len(rec["error"]), 300)
        self.assertTrue(rec["when"].endswith("+00:00"))
        self.assertIsNone(failures.last("closed", "x"))
        failures.clear("open", "x")
        self.assertIsNone(failures.last("open", "x"))
        failures.clear("open", "x")  # clearing twice is fine


class Catalog(unittest.TestCase):
    def test_rows_carry_status_fields(self):
        systems = [{**GOOD, "id": "a"}, {**GOOD, "id": "b", "status_note": "Not run yet."},
                   {**GOOD, "id": "c", "status": "superseded", "superseded_by": "a"}, {**GOOD, "id": "d"}]
        board = [{"system": "a", "open": {"scores": {"overall": 0.5, "e1_text": 0.5, "e2_table_teds": 0.5,
                                                    "e3_formula": 0.5}, "counts": {"pages": 3}}}]
        fails = {("closed", "d"): {"when": "2026-02-01T00:00:00+00:00", "error": "boom"}}
        with mock.patch("bambench.models.failures.last", lambda t, i: fails.get((t, i))), \
                mock.patch("bambench.models._speed", lambda t, i: None):
            rows = {r["id"]: r for r in models.catalog(systems, board)["systems"]}
        self.assertEqual(rows["a"]["status"], "active")
        self.assertEqual((rows["b"]["status"], rows["b"]["status_note"]), ("pending", "Not run yet."))
        self.assertEqual((rows["c"]["status"], rows["c"]["superseded_by"]), ("superseded", "a"))
        self.assertEqual((rows["d"]["status"], rows["d"]["status_note"]), ("failed", "boom"))
        self.assertEqual(rows["d"]["failure"], {"open": None, "closed": fails[("closed", "d")]})
        self.assertIsNone(rows["a"]["superseded_by"])
        self.assertIn("handles", rows["a"])  # existing fields stay


class Converters(unittest.TestCase):
    def test_olmocr_front_matter_is_dropped(self):
        reply = "---\nprimary_language: de\nis_table: true\n---\n# Prüfbericht\n\nText"
        self.assertEqual(front_matter(reply), "# Prüfbericht\n\nText")
        self.assertEqual(front_matter("# No header"), "# No header")

    def test_unlimited_ocr_det_tags_are_dropped(self):
        reply = "<|det|>title [[10, 20, 300, 40]]<|/det|>\n# Bericht\n<|det|>text [[1,2,3,4]]<|/det|>\nInhalt"
        self.assertEqual(deepseek_grounding(reply), "# Bericht\n\nInhalt")


class EmptyPrompt(unittest.TestCase):
    def test_image_only_request_when_prompt_is_empty(self):
        s = VllmVlm({"id": "x", "model": "m", "base_url": "http://127.0.0.1:1/v1"})
        sent = {}

        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b'{"choices":[{"message":{"content":"ok"},"finish_reason":"stop"}]}'

        def fake_open(req, timeout=None):
            sent.update(json.loads(req.data))
            return Resp()

        with mock.patch("bambench.systems.vllm_vlm._OPENER.open", fake_open):
            self.assertEqual(s._chat("AAAA", ""), "ok")
        self.assertEqual([p["type"] for p in sent["messages"][0]["content"]], ["image_url"])


if __name__ == "__main__":
    unittest.main()
