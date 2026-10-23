"""Turn a model's native page output into the benchmark's Markdown.

Most systems answer in Markdown. Some answer in their own format: DeepSeek-OCR 2 wraps blocks
in grounding tags, dots.mocr returns a JSON list of layout cells, Granite-Docling returns
DocTags. Each converter keeps text, HTML tables and LaTeX formulas and drops what the
annotation rules leave out (running headers, footers, pictures).
"""
from __future__ import annotations

import json
import re

_FENCE = re.compile(r"^```(?:markdown|json|html)?\s*|\s*```$")
_GROUNDING = re.compile(r"<\|ref\|>.*?<\|/ref\|>\s*<\|det\|>.*?<\|/det\|>", re.S)
_SPECIAL = re.compile(r"<\|[^|>]{1,40}\|>|<｜[^｜>]{1,40}｜>")
DOTS_DROP = {"Page-header", "Page-footer", "Picture"}


def markdown(text: str) -> str:
    return _FENCE.sub("", text.strip())


def deepseek_grounding(text: str) -> str:
    """Strip <|ref|>kind<|/ref|><|det|>[[boxes]]<|/det|> markers, keep the content after each."""
    out = _SPECIAL.sub("", _GROUNDING.sub("", markdown(text)))
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def dots_layout(text: str) -> str:
    """dots.mocr layout JSON (cells with bbox, category, text) in reading order to Markdown."""
    raw = markdown(text)
    try:
        cells = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", raw, re.S)
        if not m:
            return raw  # not JSON at all: keep what the model wrote so the score shows it
        try:
            cells = json.loads(m.group(0))
        except json.JSONDecodeError:
            return raw
    if isinstance(cells, dict):
        cells = cells.get("layout") or cells.get("cells") or cells.get("elements") or [cells]
    parts = []
    for c in cells if isinstance(cells, list) else []:
        if not isinstance(c, dict) or c.get("category") in DOTS_DROP:
            continue
        t = str(c.get("text") or "").strip()
        if not t:
            continue
        if c.get("category") == "Formula" and not t.startswith("$$"):
            t = "$$\n" + t.strip("$ \n") + "\n$$"
        parts.append(t)
    return "\n\n".join(parts)


def doctags(text: str, image_path=None) -> str:
    """Granite-Docling DocTags to Markdown via docling-core."""
    from docling_core.types.doc import DoclingDocument
    from docling_core.types.doc.document import DocTagsDocument
    from PIL import Image

    images = [Image.open(image_path)] if image_path else [None]
    tags = DocTagsDocument.from_doctags_and_image_pairs([markdown(text)], images)
    return DoclingDocument.load_from_doctags(tags, document_name="page").export_to_markdown()


CONVERTERS = {"markdown": markdown, "deepseek_grounding": deepseek_grounding, "dots_layout": dots_layout}
