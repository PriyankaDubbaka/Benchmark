"""CPU floor baseline: Poppler layout text as Markdown, plus the starter's certificate rules.

The record rules were written with BAM-S005c visible. They are a smoke test, not a model.
"""
from __future__ import annotations

import re

from ..corpus import Document, page_texts
from .base import Progress, System

NUM = r"(\d+(?:\.\d+)?)"
WITH_OXIDE = re.compile(r"^\s*([A-Z][a-z]?)\s+\(([A-Za-z0-9]+)\)\s+" + NUM + r"\s+\(" + NUM + r"\)\s+" + NUM + r"\s*$")
ELEMENTAL = re.compile(r"^\s*([A-Z][a-z]?)\s+" + NUM + r"\s+" + NUM + r"\s*$")


def extract_summary(pages: list[tuple[int, str]]) -> list[dict]:
    rows = []
    for page, text in pages:
        if page > 2:
            continue
        k = re.search(r"coverage factor of k\s*=\s*(\d+(?:\.\d+)?)", text, re.I)
        if not k:
            continue
        cf = float(k.group(1))
        cf = int(cf) if cf.is_integer() else cf
        unit, status = "%", "certified"
        for line in text.split("\n"):
            if re.search(r"Values for Information", line, re.I):
                status = "information_only"
            if "in mg/kg" in line:
                unit = "mg/kg"
            m, n = WITH_OXIDE.match(line), ELEMENTAL.match(line)
            base = {"unit": unit, "status": status, "coverage_factor": cf, "source_page": page}
            if m:
                rows.append({"element": m[1], "oxide_formula": m[2], "value": m[3], "oxide_value": m[4],
                             "expanded_uncertainty": m[5], **base})
            elif n:
                rows.append({"element": n[1], "value": n[2], "expanded_uncertainty": n[3],
                             "oxide_formula": None, "oxide_value": None, **base})
    seen, out = set(), []
    for r in rows:
        if r["element"] not in seen:
            seen.add(r["element"])
            out.append(r)
    return out


class PdftotextRules(System):
    kind = "pdftotext_rules"

    def predict(self, doc: Document, pages: list[int], progress: Progress) -> dict:
        texts = page_texts(doc)
        out = {}
        for p in pages:
            lines = [re.sub(r"\s{2,}", "  ", l).strip() for l in texts[p - 1].split("\n")]
            out[p] = "\n".join(lines)
            progress(f"page {p}")
        records = extract_summary([(p, texts[p - 1]) for p in range(1, doc.page_count + 1)])
        return {"pages": out, "records": records}
