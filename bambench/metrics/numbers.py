"""Number fidelity: are the printed numbers of a page reproduced digit for digit?

A measurement value with one wrong digit is a wrong value, and edit distance hardly notices:
0.587 against 0.578 costs two characters on a page of two thousand. This counts the numbers on
the gold page and how many of them the output holds, as printed. A decimal comma stays a comma.

Only free-standing numbers count. Digits inside a name (S005c, Al2O3, C10) belong to the text
score. Signs are left out, because a range such as 913-915 would otherwise read as a negative.
"""
from __future__ import annotations

import re
from collections import Counter
from html.parser import HTMLParser

from .text import normalize_text

_NUMBER = re.compile(r"(?<![A-Za-z0-9.,])\d+(?:[.,]\d+)*(?![A-Za-z0-9])")


class _Cells(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = [""]

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ("td", "th", "tr", "br", "p", "div", "li"):
            self.parts.append("")  # a new cell or line never joins two numbers

    def handle_data(self, data):
        self.parts[-1] += data


def numbers(parts: dict) -> Counter:
    """Every free-standing number in a split page (see markdown.split), with its count."""
    found: Counter = Counter(_NUMBER.findall(normalize_text(parts["text"])))
    for table in parts["tables"]:
        p = _Cells()
        p.feed(table)
        for cell in p.parts:
            found.update(_NUMBER.findall(normalize_text(cell, cell=True)))
    return found


def compare(gold: dict, pred: dict) -> dict:
    g, p = numbers(gold), numbers(pred)
    return {"gold": sum(g.values()), "pred": sum(p.values()), "matched": sum((g & p).values())}
