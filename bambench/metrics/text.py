"""Edit distance on normalised text.

Levenshtein uses Hyyrö's bit-parallel algorithm on Python ints, so whole pages compare in
milliseconds without a compiled dependency.
"""
from __future__ import annotations

import re
import unicodedata


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    m = len(b)
    if m == 0:
        return len(a)
    peq: dict[str, int] = {}
    for i, c in enumerate(b):
        peq[c] = peq.get(c, 0) | (1 << i)
    full = (1 << m) - 1
    last = 1 << (m - 1)
    pv, mv, score = full, 0, m
    for c in a:
        eq = peq.get(c, 0)
        xv = eq | mv
        xh = ((((eq & pv) + pv) & full) ^ pv) | eq
        ph = (mv | ~(xh | pv)) & full
        mh = pv & xh
        if ph & last:
            score += 1
        elif mh & last:
            score -= 1
        ph = ((ph << 1) | 1) & full
        mh = (mh << 1) & full
        pv = (mh | ~(xv | ph)) & full
        mv = ph & xv
    return score


def ned(a: str, b: str) -> float:
    """Normalised edit distance in [0, 1]. Two empty strings are identical."""
    if not a and not b:
        return 0.0
    return levenshtein(a, b) / max(len(a), len(b))


_MD = re.compile(r"(^|\s)#{1,6}\s|[*_`>]|!\[[^\]]*\]\([^)]*\)|<[^>]+>")
_WS = re.compile(r"\s+")


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = _MD.sub(" ", s)
    return _WS.sub(" ", s).strip()


def normalize_formula(s: str) -> str:
    """Drop spacing commands, sizing and grouping braces, which do not change the rendered formula."""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\\(?:left|right|displaystyle|quad|qquad)(?![A-Za-z])|\\[,;:! ]", "", s)
    s = re.sub(r"\\(?:mathrm|text|operatorname)(?![A-Za-z])", "", s)
    return re.sub(r"[\s{}]", "", s)
