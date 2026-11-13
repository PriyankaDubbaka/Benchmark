"""The About page: version, licence, how to cite and contact, read from the repository files.

CITATION.cff is read by a small reader for the few shapes this file uses, so no YAML library is
needed: top-level `key: value` pairs, a folded `abstract: >-` block, and lists of authors and contacts.
"""
from __future__ import annotations

from datetime import date

from . import __version__
from .metrics import SCORER_VERSION
from .paths import ROOT


def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def _split(line: str) -> tuple[str, str] | None:
    key, sep, val = line.partition(":")
    return (key.strip(), _unquote(val)) if sep and key.strip() else None


def parse_cff(text: str) -> dict:
    """Top-level scalars plus the `authors` and `contact` lists (each a list of dicts)."""
    out: dict = {"authors": [], "contact": []}
    lst: list | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] in " \t-":  # indented: belongs to the block above
            if lst is None:
                continue  # inside a folded block or a list we do not read
            line = raw.strip()
            if line.startswith("- "):
                lst.append({})
                line = line[2:]
            kv = _split(line)
            if kv and lst:
                lst[-1][kv[0]] = kv[1]
            continue
        lst = None
        kv = _split(raw)
        if not kv:
            continue
        if kv[0] in ("authors", "contact") and not kv[1]:
            lst = out[kv[0]]
        else:
            out[kv[0]] = "" if kv[1] in (">", ">-", "|", "|-") else kv[1]
    return out


def _initials(given: str) -> str:
    return " ".join(p[0] + "." for p in given.replace("-", " ").split() if p)


def _citation(cff: dict) -> str:
    names = []
    for a in cff["authors"]:
        family, given = a.get("family-names", ""), a.get("given-names", "")
        names.append(f"{family}, {_initials(given)}".strip(", ") if family else a.get("name", ""))
    names = [n for n in names if n]
    who = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1] if names else ""
    year = (cff.get("date-released") or "")[:4] or str(date.today().year)
    org = next((a["affiliation"] for a in cff["authors"] if a.get("affiliation")), "")
    parts = [f"{who} ({year})." if who else f"({year}).", f"{cff.get('title', '')}, version {cff.get('version', __version__)}."]
    if org:
        parts.append(f"{org}.")
    return " ".join(parts)


def _read(path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def about() -> dict:
    licence = None
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt"):
        text = _read(ROOT / name)
        licence = next((l.strip() for l in (text or "").splitlines() if l.strip()), None)
        if licence:
            break
    cff_text = _read(ROOT / "CITATION.cff") or ""
    cff = parse_cff(cff_text)
    contact = next((c.get("email") or c.get("name") for c in cff["contact"] if c.get("email") or c.get("name")), None)
    return {"version": __version__, "scorer": SCORER_VERSION, "license": licence, "contact": contact,
            "repository": cff.get("repository-code") or None,
            "citation": {"text": _citation(cff) if cff_text else "", "cff": cff_text},
            "changelog": _read(ROOT / "docs" / "CHANGELOG.md") or ""}
