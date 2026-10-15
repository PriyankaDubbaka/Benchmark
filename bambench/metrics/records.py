"""E5 measurement records, ported from the bam-docbench-starter scorer.

Rows match on the element symbol. A record is correct only when every field matches.
Decimal strings compare after trailing-zero normalisation; numerical differences are never
excused by the measurement uncertainty. Invalid predictions are rejected, not repaired.
"""
from __future__ import annotations

import math
import re

FIELDS = ("value", "unit", "expanded_uncertainty", "coverage_factor", "status",
          "oxide_formula", "oxide_value", "source_page")
NUMERIC = ("value", "expanded_uncertainty", "oxide_value")
CRITICAL = ("unit", "status", "expanded_uncertainty")
_DEC = re.compile(r"^-?\d+(\.\d+)?$")
_FORMULA = re.compile(r"^(?:[A-Z][a-z]?\d*)+$")


class ValidationError(ValueError):
    pass


def _check(cond, msg):
    if not cond:
        raise ValidationError(msg)


def decimal(s) -> str:
    _check(isinstance(s, str) and _DEC.match(s), "Numeric values must be finite decimal strings, not floats/exponents")
    neg = s.startswith("-")
    a, _, b = s.lstrip("-").partition(".")
    a = a.lstrip("0") or "0"
    b = b.rstrip("0")
    v = a + ("." + b if b else "")
    return ("-" if neg and v != "0" else "") + v


def validate_rows(rows, page_count: int) -> None:
    _check(isinstance(rows, list), "records must be an array")
    seen = set()
    for r in rows:
        _check(isinstance(r, dict), "Bad record")
        _check(sorted(r) == sorted(("element",) + FIELDS), "Unexpected or missing extraction fields")
        _check(isinstance(r["element"], str) and re.match(r"^[A-Z][a-z]?$", r["element"]), "Invalid element key")
        _check(r["element"] not in seen, "Duplicate element: " + str(r["element"]))
        seen.add(r["element"])
        decimal(r["value"])
        decimal(r["expanded_uncertainty"])
        _check(r["unit"] in ("%", "mg/kg"), "Unsupported unit")
        _check(r["status"] in ("certified", "information_only"), "Invalid status")
        sp = r["source_page"]
        _check(isinstance(sp, int) and not isinstance(sp, bool) and 1 <= sp <= page_count, "Invalid source page")
        cf = r["coverage_factor"]
        _check(isinstance(cf, (int, float)) and not isinstance(cf, bool) and math.isfinite(cf) and cf > 0,
               "Invalid coverage factor")
        _check(r["oxide_formula"] is None or (isinstance(r["oxide_formula"], str) and _FORMULA.match(r["oxide_formula"])),
               "Invalid formula")
        _check((r["oxide_formula"] is None) == (r["oxide_value"] is None), "Oxide formula/value null mismatch")
        if r["oxide_value"] is not None:
            decimal(r["oxide_value"])


def _equal(k, a, b) -> bool:
    if a is None or b is None:
        return a is b
    if k in NUMERIC:
        return decimal(a) == decimal(b)
    return a == b


def score_records(gold: list, pred: list, page_count: int) -> dict:
    validate_rows(gold, page_count)
    validate_rows(pred, page_count)
    _check(len(gold) > 0, "Empty reference set")
    by_el = {r["element"]: r for r in pred}
    exact = 0
    correct = dict.fromkeys(FIELDS, 0)
    errors = []
    critical = dict.fromkeys(CRITICAL, 0)
    for g in gold:
        p = by_el.get(g["element"])
        wrong = []
        for f in FIELDS:
            if p is not None and _equal(f, g[f], p[f]):
                correct[f] += 1
            else:
                wrong.append(f)
                if p is not None and f in critical:
                    critical[f] += 1
        if wrong:
            errors.append({"element": g["element"], "fields": wrong})
        else:
            exact += 1
    precision = exact / len(pred) if pred else 0.0
    recall = exact / len(gold)
    gold_el = {g["element"] for g in gold}
    return {
        "gold_records": len(gold),
        "predicted_records": len(pred),
        "exact_records": exact,
        "record_precision": precision,
        "record_recall": recall,
        "record_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "field_accuracy_over_all_gold_records": {f: correct[f] / len(gold) for f in FIELDS},
        "critical_errors": {"wrong_unit": critical["unit"], "wrong_status": critical["status"],
                            "wrong_uncertainty": critical["expanded_uncertainty"]},
        "extra_elements": [r["element"] for r in pred if r["element"] not in gold_el],
        "errors": errors,
    }
