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
    def test_thought_blocks_and_answer_boxes_are_stripped(self):
        from bambench.systems.outputs import markdown
        self.assertEqual(markdown("<|channel>thought\n<channel|># Bericht\n\nText"), "# Bericht\n\nText")
        self.assertEqual(markdown("<think>\nplan\n</think>\n\n# Bericht"), "# Bericht")
        self.assertEqual(markdown("<|begin_of_box|>```markdown\n# Bericht\n```<|end_of_box|>"), "# Bericht")

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


class Notation(unittest.TestCase):
    """The same printed text must compare equal however a system spells it."""

    def test_subscripts_compare_equal_in_any_notation(self):
        from bambench.metrics.text import normalize_text as n
        self.assertEqual(n("C<sub>10</sub>H<sub>8</sub>"), "C10H8")
        self.assertEqual(n("C$_{10}$H$_8$"), "C10H8")
        self.assertEqual(n("C\u2081\u2080H\u2088"), "C10H8")
        self.assertEqual(n("$\\mathrm{Al_2O_3}$"), "Al2O3")
        self.assertEqual(n("10<sup>-3</sup>"), n("10$^{-3}$"))

    def test_dashes_quotes_and_soft_hyphens(self):
        from bambench.metrics.text import normalize_text as n
        self.assertEqual(n("913\u2013915 \u00b0C"), "913-915 \u00b0C")
        self.assertEqual(n("\u22120.5"), "-0.5")
        self.assertEqual(n("\u201ePr\u00fcf\u201c"), '"Pr\u00fcf"')
        self.assertEqual(n("Konservie\u00adrung"), "Konservierung")

    def test_inline_math_units_read_as_text(self):
        from bambench.metrics.text import normalize_text as n
        self.assertEqual(n("$5\\,\\mu\\mathrm{m}$ thick"), n("5 \u00b5m thick"))
        self.assertEqual(n("$\\pm$ 0.5"), "\u00b1 0.5")

    def test_comparison_signs_survive(self):
        from bambench.metrics.text import normalize_text as n
        self.assertEqual(n("x < 5 and y > 3"), "x < 5 and y > 3")
        self.assertEqual(n("&lt; 0.5 mg/kg"), "< 0.5 mg/kg")
        self.assertEqual(n("> quoted line"), "quoted line")
        self.assertEqual(n("> 10", cell=True), "> 10")

    def test_table_cells_keep_signs_and_join_notations(self):
        a = "<table><tr><td>&gt; 10</td><td>(Al<sub>2</sub>O<sub>3</sub>)</td><td>Mass fraction<br>in %</td></tr></table>"
        b = "<table><tr><td>> 10</td><td>(Al$_2$O$_3$)</td><td>Mass fraction in %</td></tr></table>"
        self.assertEqual(teds(a, b), 1.0)
        c = "<table><tr><td>10</td><td>(Al2O3)</td><td>Mass fraction in %</td></tr></table>"
        self.assertLess(teds(a, c), 1.0)

    def test_block_tags_still_separate_words(self):
        from bambench.metrics.text import normalize_text as n
        self.assertEqual(n("<p>one</p><p>two</p>"), "one two")
        self.assertEqual(n("a<br>b"), "a b")


class Numbers(unittest.TestCase):
    """Number fidelity: printed numbers must come back digit for digit."""

    def _n(self, md):
        from bambench.metrics.numbers import numbers
        return dict(numbers(split(md)))

    def test_one_wrong_digit_is_a_miss(self):
        gold = "<table><tr><td>Al</td><td>0.587</td><td>0.018</td></tr></table>\n\nk = 2, about 95 %"
        good = score_page(gold, gold)["numbers"]
        self.assertEqual(good, {"gold": 4, "pred": 4, "matched": 4})
        bad = score_page(gold, gold.replace("0.587", "0.578"))["numbers"]
        self.assertEqual(bad, {"gold": 4, "pred": 4, "matched": 3})

    def test_digits_inside_names_do_not_count(self):
        self.assertEqual(self._n("BAM-S005c, Al<sub>2</sub>O<sub>3</sub>, C10 and ISO 17034"), {"17034": 1})

    def test_neighbouring_cells_do_not_merge(self):
        self.assertEqual(self._n("<table><tr><td>40</td><td>0.982</td></tr></table>"), {"40": 1, "0.982": 1})

    def test_decimal_comma_is_kept_as_printed(self):
        s = score_page("Ethanol 1,0291 g/l", "Ethanol 1.0291 g/l")["numbers"]
        self.assertEqual(s["matched"], 0)

    def test_repeats_are_counted(self):
        s = score_page("2.7 and 2.7 and 5", "2.7 and 5")["numbers"]
        self.assertEqual(s, {"gold": 3, "pred": 2, "matched": 2})

    def test_ranges_and_dates(self):
        self.assertEqual(self._n("913–915 °C on 2020-08-19"), {"913": 1, "915": 1, "2020": 1, "08": 1, "19": 1})
