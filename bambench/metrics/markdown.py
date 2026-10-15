"""Split page Markdown into text, tables and display formulas."""
from __future__ import annotations

import html
import re

_HTML_TABLE = re.compile(r"<table\b.*?</table>", re.S | re.I)
_FORMULA = re.compile(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]", re.S)
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def pipe_to_html(lines: list[str]) -> str:
    rows = [_cells(l) for l in lines if not _SEP.match(l)]
    body = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table>{body}</table>"


def split(md: str) -> dict:
    md = _COMMENT.sub("", md or "")
    tables: list[str] = []

    def keep_table(m):
        tables.append(m.group(0))
        return "\n"

    md = _HTML_TABLE.sub(keep_table, md)
    formulas: list[str] = []

    def keep_formula(m):
        formulas.append((m.group(1) or m.group(2)).strip())
        return "\n"

    md = _FORMULA.sub(keep_formula, md)

    text_lines: list[str] = []
    block: list[str] = []
    lines = md.split("\n")
    for i, line in enumerate(lines):
        is_row = line.strip().startswith("|") and line.count("|") >= 2
        if is_row:
            block.append(line)
            continue
        if block:
            if len(block) >= 2 and any(_SEP.match(b) for b in block):
                tables.append(pipe_to_html(block))
            else:
                text_lines.extend(block)
            block = []
        text_lines.append(line)
    if block:
        if len(block) >= 2 and any(_SEP.match(b) for b in block):
            tables.append(pipe_to_html(block))
        else:
            text_lines.extend(block)
    return {"text": "\n".join(text_lines), "tables": tables, "formulas": formulas}
