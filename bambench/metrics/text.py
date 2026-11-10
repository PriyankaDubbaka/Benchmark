"""Edit distance on normalised text.

Levenshtein uses Hyyrö's bit-parallel algorithm on Python ints, so whole pages compare in
milliseconds without a compiled dependency.
"""
from __future__ import annotations

import html
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


# Notation that prints the same must compare the same. A subscript can arrive as <sub>2</sub>,
# as $_2$ or as the Unicode character; a range as 913-915 with any of six dash characters.
_INLINE_TAG = re.compile(r"</?(?:sub|sup|b|i|em|strong|u|s|span|font|small|mark)\b[^<>]*>", re.I)
_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9]*(?:\s[^<>]*)?/?>")
_MATH = re.compile(r"(?<![\\$])\$([^$\n]+?)\$(?!\$)")
_MATH_FONT = re.compile(r"\\(?:mathrm|mathbf|mathit|mathsf|text|textrm|operatorname)(?![A-Za-z])")
_MATH_SPACE = re.compile(r"\\[,;:! ]|~")
_MATH_SYMBOL = re.compile(r"\\([A-Za-z]+|%)")
_SYMBOLS = {
    "mu": "μ", "pm": "±", "times": "×", "cdot": "·", "%": "%", "circ": "°", "degree": "°",
    "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "approx": "≈", "sim": "~", "neq": "≠",
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "Delta": "Δ", "lambda": "λ",
    "sigma": "σ", "rho": "ρ", "theta": "θ", "omega": "ω", "Omega": "Ω", "pi": "π",
}
_CHARS = str.maketrans({
    **{c: "-" for c in "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"},  # hyphens, dashes, minus
    **{c: '"' for c in "\u201c\u201d\u201e\u201f\u00ab\u00bb"},  # curly, low and angle quotes
    **{c: "'" for c in "\u2018\u2019\u201a\u201b"},
    "\u00ad": None,  # soft hyphen
})
_HEADING = re.compile(r"(^|\s)#{1,6}\s")
_QUOTE = re.compile(r"^[ \t]*(?:>[ \t]?)+", re.M)
_MARKS = re.compile(r"[*_`]")
_WS = re.compile(r"\s+")


def _plain_math(m: re.Match) -> str:
    s = _MATH_SPACE.sub(" ", _MATH_FONT.sub("", m.group(1)))
    s = _MATH_SYMBOL.sub(lambda k: _SYMBOLS.get(k.group(1), k.group(0)), s)
    return re.sub(r"[_^{}]", "", s)


def normalize_text(s: str, cell: bool = False) -> str:
    """Text as it is compared. `cell` is for table cells: the HTML parser has already removed
    their tags and entities, and a cell cannot hold a block quote, so a leading > stays."""
    if not cell:
        # Tags go before entities are unescaped, so a written &lt;td&gt; stays text.
        s = _TAG.sub(" ", _INLINE_TAG.sub("", s))
        s = _QUOTE.sub("", html.unescape(s))
    s = unicodedata.normalize("NFKC", s).translate(_CHARS)
    s = _MATH.sub(_plain_math, s)
    s = _MARKS.sub(" ", _HEADING.sub(" ", s))
    return _WS.sub(" ", s).strip()


def normalize_formula(s: str) -> str:
    """Drop spacing commands, sizing and grouping braces, which do not change the rendered formula."""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\\(?:left|right|displaystyle|quad|qquad)(?![A-Za-z])|\\[,;:! ]", "", s)
    s = re.sub(r"\\(?:mathrm|text|operatorname)(?![A-Za-z])", "", s)
    return re.sub(r"[\s{}]", "", s)
