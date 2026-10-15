"""Port of the starter's 18 scorer tests (bam-docbench-starter/tests/score.test.ts)."""
import copy
import json
import unittest
from pathlib import Path

from bambench.metrics.records import ValidationError, decimal, score_records
from bambench.metrics.retrieval import score_retrieval
from bambench.systems.pdftotext_rules import extract_summary

GOLD = Path(__file__).resolve().parent.parent / "data/open/annotations/bam-s005c-v2"
EG = json.loads((GOLD / "records.json").read_text())["records"]
RG = json.loads((GOLD / "queries.json").read_text())["queries"]


def ideal():
    return [{"query_id": q["id"], "pages": [int(p) for p in sorted(q["relevance"], key=lambda p: -q["relevance"][p])]}
            for q in RG]


class Records(unittest.TestCase):
    def test_exact_reference_scores_one(self):
        self.assertEqual(score_records(EG, EG, 8)["record_f1"], 1)

    def test_empty_is_zero(self):
        self.assertEqual(score_records(EG, [], 8)["record_f1"], 0)

    def test_wrong_unit_not_equivalent(self):
        p = copy.deepcopy(EG); p[0]["unit"] = "mg/kg"
        r = score_records(EG, p, 8)
        self.assertLess(r["record_f1"], 1)
        self.assertEqual(r["critical_errors"]["wrong_unit"], 1)

    def test_uncertainty_is_not_a_tolerance(self):
        p = copy.deepcopy(EG)
        p[0]["value"] = str(float(p[0]["value"]) + float(p[0]["expanded_uncertainty"]) / 2)
        self.assertLess(score_records(EG, p, 8)["record_f1"], 1)

    def test_wrong_information_status_fails(self):
        p = copy.deepcopy(EG)
        next(r for r in p if r["status"] == "information_only")["status"] = "certified"
        self.assertLess(score_records(EG, p, 8)["record_f1"], 1)

    def test_wrong_page_fails(self):
        p = copy.deepcopy(EG); p[0]["source_page"] = 8
        self.assertLess(score_records(EG, p, 8)["record_f1"], 1)

    def test_duplicate_rejected(self):
        with self.assertRaises(ValidationError):
            score_records(EG, EG + [EG[0]], 8)

    def test_missing_field_rejected(self):
        p = copy.deepcopy(EG); del p[0]["unit"]
        with self.assertRaises(ValidationError):
            score_records(EG, p, 8)

    def test_decimal_trailing_zero_only(self):
        self.assertEqual(decimal("033.100"), "33.1")
        with self.assertRaises(ValidationError):
            decimal("NaN")
        with self.assertRaises(ValidationError):
            decimal(0.2)

    def test_extra_element_reduces_precision(self):
        extra = {**EG[0], "element": "Xe"}
        self.assertLess(score_records(EG, EG + [extra], 8)["record_precision"], 1)


class Retrieval(unittest.TestCase):
    def test_ideal_scores_one(self):
        a = score_retrieval(RG, ideal(), 8)["aggregate"]
        self.assertEqual((a["ndcg_at_5"], a["recall_at_5"], a["complete_evidence_at_5"]), (1, 1, 1))

    def test_empty_is_zero(self):
        a = score_retrieval(RG, [], 8)["aggregate"]
        self.assertEqual((a["recall_at_5"], a["mrr_at_5"]), (0, 0))

    def test_duplicate_pages_rejected(self):
        p = ideal(); p[0]["pages"] = [1, 1]
        with self.assertRaises(ValidationError):
            score_retrieval(RG, p, 8)

    def test_unknown_query_rejected(self):
        with self.assertRaises(ValidationError):
            score_retrieval(RG, [{"query_id": "UNKNOWN", "pages": [1]}], 8)

    def test_invalid_page_rejected(self):
        p = ideal(); p[0]["pages"] = [9]
        with self.assertRaises(ValidationError):
            score_retrieval(RG, p, 8)

    def test_duplicate_query_rejected(self):
        p = ideal()
        with self.assertRaises(ValidationError):
            score_retrieval(RG, p + [p[0]], 8)

    def test_partial_multi_page_evidence_not_complete(self):
        q = next(q for q in RG if len(q["evidence_pages"]) > 1)
        a = score_retrieval([q], [{"query_id": q["id"], "pages": [q["evidence_pages"][0]]}], 8)["aggregate"]
        self.assertEqual(a["complete_evidence_at_5"], 0)
        self.assertLess(a["recall_at_5"], 1)

    def test_baseline_never_needs_gold(self):
        self.assertEqual(extract_summary([]), [])


if __name__ == "__main__":
    unittest.main()
