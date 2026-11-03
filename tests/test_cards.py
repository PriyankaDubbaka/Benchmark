import json
import shlex
import unittest
from unittest import mock

from bambench.paths import SYSTEMS
from bambench.systems import KINDS, get_system
from bambench.systems.outputs import CONVERTERS, deepseek_grounding, front_matter
from bambench.systems.vllm_vlm import VllmVlm

REQUIRED = ("id", "name", "kind", "license", "params")


class Cards(unittest.TestCase):
    def test_every_card_is_complete_and_loads(self):
        kinds = {k.kind for k in KINDS} if not isinstance(KINDS, dict) else set(KINDS)
        for f in sorted(SYSTEMS.glob("*.json")):
            with self.subTest(card=f.name):
                c = json.loads(f.read_text(encoding="utf-8"))
                self.assertEqual(c["id"], f.stem)
                for k in REQUIRED:
                    self.assertIn(k, c)
                self.assertIn(c["kind"], kinds)
                if c.get("serve"):
                    self.assertIn("model", c)
                self.assertIn(c.get("output", "markdown"), CONVERTERS | {"doctags": None})
                if c.get("serve"):
                    self.assertTrue(shlex.split(c["serve"])[0] == "vllm")  # parses as the job will eval it
                    self.assertNotIn("--port", c["serve"])
                get_system(c["id"])


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
