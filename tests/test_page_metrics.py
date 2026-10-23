import json
import random
import unittest
from pathlib import Path

from bambench.metrics.markdown import split
from bambench.metrics.page import score_page
from bambench.metrics.teds import teds
from bambench.metrics.text import levenshtein, ned

PAGE1 = json.loads((Path(__file__).resolve().parent.parent /
                    "data/open/annotations/bam-s005c-v2/page-001.json").read_text())["markdown"]


def naive(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


class Text(unittest.TestCase):
    def test_bitparallel_matches_dynamic_programming(self):
        rng = random.Random(7)
        for _ in range(2000):
            a = "".join(rng.choice("abcé ") for _ in range(rng.randint(0, 15)))
            b = "".join(rng.choice("abcd ") for _ in range(rng.randint(0, 15)))
            self.assertEqual(levenshtein(a, b), naive(a, b), (a, b))

    def test_ned_bounds(self):
        self.assertEqual(ned("", ""), 0)
        self.assertEqual(ned("abc", ""), 1)


class Tables(unittest.TestCase):
    def test_identical_tables_score_one(self):
        t = split(PAGE1)["tables"][0]
        self.assertEqual(teds(t, t), 1.0)

    def test_pipe_and_html_tables_compare_equal(self):
        pipe = "| a | b |\n|---|---|\n| 1 | 2 |"
        html = "<table><thead><tr><th>a</th><th>b</th></tr></thead><tr><td>1</td><td>2</td></tr></table>"
        self.assertEqual(teds(split(pipe)["tables"][0], html), 1.0)

    def test_wrong_cell_lowers_teds_but_not_structure(self):
        a = "<table><tr><td>Al</td><td>0.587</td></tr></table>"
        b = "<table><tr><td>Al</td><td>0.578</td></tr></table>"
        self.assertLess(teds(a, b), 1.0)
        self.assertEqual(teds(a, b, structure_only=True), 1.0)

    def test_missing_span_changes_structure(self):
        a = "<table><tr><td colspan='2'>Element</td></tr><tr><td>Al</td><td>Al2O3</td></tr></table>"
        b = "<table><tr><td>Element</td></tr><tr><td>Al</td><td>Al2O3</td></tr></table>"
        self.assertLess(teds(a, b, structure_only=True), 1.0)


class Page(unittest.TestCase):
    def test_gold_against_itself_is_perfect(self):
        s = score_page(PAGE1, PAGE1)
        self.assertEqual(s["text_score"], 1.0)
        self.assertEqual([t["teds"] for t in s["tables"]], [1.0])

    def test_missing_table_scores_zero(self):
        s = score_page(PAGE1, "Certified Reference Material")
        self.assertEqual(s["tables"][0]["teds"], 0.0)

    def test_formulas_are_matched(self):
        s = score_page("Text\n\n$$E = mc^2$$", "Text\n\n$$E=mc^{2}$$")
        self.assertGreater(s["formulas"][0], 0.7)


if __name__ == "__main__":
    unittest.main()


class Pairing(unittest.TestCase):
    def test_structure_score_uses_the_content_pairing(self):
        g1 = "<table><tr><td>Al</td><td>0.587</td></tr></table>"
        g2 = "<table><tr><td colspan='2'>Values</td></tr></table>"
        s = score_page("Text\n\n" + g1 + "\n\n" + g2, "Text\n\n" + g1)
        self.assertEqual(s["tables"][0], {"teds": 1.0, "teds_struct": 1.0})
        self.assertEqual(s["tables"][1], {"teds": 0.0, "teds_struct": 0.0})


class Figures(unittest.TestCase):
    def test_figure_placeholders_are_not_scored_as_text(self):
        from bambench.metrics.markdown import split
        parts = split("Fig. 2: Trunnion clearance\n\n![figure](fig-2.png)\n<img src='x.png'>")
        self.assertEqual(parts["text"].split(), ["Fig.", "2:", "Trunnion", "clearance"])


class NativeOutputs(unittest.TestCase):
    def test_deepseek_grounding_tags_are_stripped(self):
        from bambench.systems.outputs import deepseek_grounding
        raw = "<|ref|>title<|/ref|><|det|>[[10, 10, 200, 40]]<|/det|>\n# Prüfbericht\n\n<|ref|>image<|/ref|><|det|>[[1,2,3,4]]<|/det|>\n\nText"
        self.assertEqual(deepseek_grounding(raw), "# Prüfbericht\n\nText")

    def test_dots_layout_json_becomes_markdown_in_order(self):
        from bambench.systems.outputs import dots_layout
        raw = json.dumps([
            {"bbox": [0, 0, 1, 1], "category": "Page-header", "text": "GNB"},
            {"bbox": [0, 1, 1, 2], "category": "Title", "text": "# Scope"},
            {"bbox": [0, 2, 1, 3], "category": "Picture"},
            {"bbox": [0, 3, 1, 4], "category": "Formula", "text": "E = mc^2"},
            {"bbox": [0, 4, 1, 5], "category": "Table", "text": "<table><tr><td>a</td></tr></table>"},
        ])
        self.assertEqual(dots_layout("```json\n" + raw + "\n```"),
                         "# Scope\n\n$$\nE = mc^2\n$$\n\n<table><tr><td>a</td></tr></table>")

    def test_dots_layout_keeps_text_that_is_not_json(self):
        from bambench.systems.outputs import dots_layout
        self.assertEqual(dots_layout("plain words"), "plain words")

    def test_every_card_has_a_known_kind_and_output(self):
        from bambench.systems import KINDS, load_cards
        from bambench.systems.outputs import CONVERTERS
        for card in load_cards():
            self.assertIn(card["kind"], KINDS, card["id"])
            self.assertIn(card.get("output", "markdown"), {*CONVERTERS, "doctags"}, card["id"])
            self.assertIn("handles", card, card["id"])
