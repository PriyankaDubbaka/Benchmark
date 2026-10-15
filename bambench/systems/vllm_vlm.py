"""A vision-language model served by vLLM on the same machine or a whitelisted BAM host.

Sends one rendered page image per request to an OpenAI-compatible endpoint. Refuses any
host that is not localhost or listed in BAMBENCH_ALLOWED_HOSTS, so a typo in a card can
never ship a confidential page to the internet.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from ..corpus import Document, page_image
from ..metrics.records import ValidationError, validate_rows
from .base import Progress, System

PAGE_PROMPT = """Convert this document page to Markdown.
- Keep the reading order. Use # headings for titles.
- Write every table as an HTML <table> with <tr> and <td>; use colspan/rowspan for merged cells.
- Write display formulas as LaTeX between $$ and $$.
- Leave out running page headers, footers and page numbers.
Return only the Markdown."""

RECORDS_PROMPT = """This is page {page} of a reference-material certificate.
Extract every elemental measurement row from the certified summary table or the
'values for information' table on this page. Ignore individual laboratory results.
Return only a JSON array. Each object has exactly these keys:
element (symbol, e.g. "Al"), value (decimal string), unit ("%" or "mg/kg"),
expanded_uncertainty (decimal string), coverage_factor (number, e.g. 2),
status ("certified" or "information_only"), oxide_formula (e.g. "Al2O3" or null),
oxide_value (decimal string or null).
Return [] if the page has no such table."""

LOCAL = {"localhost", "127.0.0.1", "::1"}
# Ignore http_proxy/https_proxy: a cluster proxy would otherwise relay page images off the host.
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def allowed_host(url: str) -> bool:
    host = urlparse(url).hostname or ""
    extra = {h.strip() for h in os.environ.get("BAMBENCH_ALLOWED_HOSTS", "").split(",") if h.strip()}
    return host in LOCAL or host in extra


class VllmVlm(System):
    kind = "vllm"

    @property
    def base_url(self) -> str:
        return os.environ.get(self.card.get("base_url_env", "BAMBENCH_VLLM_URL"), self.card.get("base_url", "http://127.0.0.1:8000/v1"))

    def available(self) -> tuple[bool, str]:
        if not allowed_host(self.base_url):
            return False, f"{self.base_url} is not a local or allowed host"
        try:
            with _OPENER.open(self.base_url.rstrip("/") + "/models", timeout=3) as r:
                served = [m["id"] for m in json.load(r).get("data", [])]
        except (urllib.error.URLError, OSError, ValueError):
            return False, f"no vLLM server at {self.base_url}"
        if self.card["model"] not in served:
            return False, f"server is running {', '.join(served) or 'nothing'}, not {self.card['model']}"
        return True, ""

    def _chat(self, image_b64: str, prompt: str) -> str:
        if not allowed_host(self.base_url):
            raise PermissionError(f"Refusing to send document pages to {self.base_url}")
        body = {
            "model": self.card["model"],
            "temperature": 0,
            "max_tokens": self.card.get("max_tokens", 4096),
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                {"type": "text", "text": prompt},
            ]}],
        }
        req = urllib.request.Request(self.base_url.rstrip("/") + "/chat/completions",
                                     data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with _OPENER.open(req, timeout=self.card.get("timeout_s", 600)) as r:
            return json.load(r)["choices"][0]["message"]["content"] or ""

    def predict(self, doc: Document, pages: list[int], progress: Progress) -> dict:
        out, records, raw = {}, [], {}
        dpi = self.card.get("dpi", 144)
        for p in pages:
            img = base64.b64encode(page_image(doc, p, dpi).read_bytes()).decode()
            t = time.time()
            md = self._chat(img, self.card.get("page_prompt", PAGE_PROMPT))
            out[p] = re.sub(r"^```(?:markdown)?\s*|\s*```$", "", md.strip())
            if self.card.get("records") and doc.doc_type == "certificate":
                reply = self._chat(img, RECORDS_PROMPT.format(page=p))
                raw[p] = reply
                records.extend(self._parse_records(reply, p, doc.page_count))
            progress(f"page {p} in {time.time() - t:.1f}s")
        seen, dedup = set(), []
        for r in records:
            if r["element"] not in seen:
                seen.add(r["element"])
                dedup.append(r)
        return {"pages": out, "records": dedup if self.card.get("records") else None, "raw_records": raw}

    @staticmethod
    def _parse_records(reply: str, page: int, page_count: int) -> list[dict]:
        m = re.search(r"\[.*\]", reply, re.S)
        if not m:
            return []
        try:
            items = json.loads(m.group(0))
        except json.JSONDecodeError:
            return []
        keep = []
        for it in items if isinstance(items, list) else []:
            if not isinstance(it, dict):
                continue
            row = {k: it.get(k) for k in ("element", "value", "unit", "expanded_uncertainty", "coverage_factor",
                                          "status", "oxide_formula", "oxide_value")}
            for k in ("value", "expanded_uncertainty", "oxide_value"):
                if isinstance(row[k], (int, float)) and not isinstance(row[k], bool):
                    row[k] = str(row[k])
            row["source_page"] = page
            try:
                validate_rows([row], page_count)
            except ValidationError:
                continue  # malformed rows are dropped and therefore count against recall
            keep.append(row)
        return keep
