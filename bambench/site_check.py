"""Leak check for a hosted copy of the dashboard.

Run it after `bambench export-site public` and before the folder is published. It fails when the
folder holds anything that has to stay inside BAM, as far as a check of the folder can tell:

- any file export-site does not write: only the site's .html/.js/.css files, config.js, the fixed
  api/*.json files and pair files named after two open-track systems on the leaderboard
- a missing api file, so an empty or half-written folder never passes
- a document id that is not in the open track, as a value or inside a list
- page text, page items or raw model outputs, which a hosted copy never carries
- a closed-track result, wherever it sits, unless it is exactly what export-closed published:
  same system, same run, same scores and page count, publishable, and 20 or more pages

Where the closed track is present on the machine (the BAM cluster or a VDI), it also reads every
closed label and closed model output and searches every string in the folder, and every file path,
for closed document ids and hashes (as whole tokens), and for closed text: any run of 8 words, or a
whole closed line or title of 3 to 7 words and 20 or more characters, even inside a longer string.
Text that also occurs in the open track is ignored, so boilerplate does not block a clean export.

What it cannot do: in CI the closed corpus is absent, so free text that is not marked as closed
cannot be recognised there. The protection in CI is that closed files never enter the repository
(the pre-commit guard and .gitignore). Run the check on the cluster or the VDI as well before
committing results; that is where the closed corpus is.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from .corpus import load_documents
from .gold import load_page, page_statuses
from .paths import SITE, published_dir, run_dir
from .runner import MIN_CLOSED_PAGES

SITE_SUFFIXES = {".html", ".js", ".css"}  # the only site files export-site copies
API_FILES = {"overview", "leaderboard", "models", "systems", "documents", "composition", "about"}
VERSUS = re.compile(r"api/versus/open/([^/]+)/([^/]+)\.json")
DOC_KEYS = {"document_id", "doc_id", "family_id"}  # values that name a document
TEXT_KEYS = {"page_items", "markdown", "prediction", "predictions"}  # page text or model output
SHINGLE = 8  # words in a run of closed text that counts as a match
SHORT = (3, SHINGLE - 1)  # word counts of whole short lines and titles that are matched too
MIN_CHARS = 20  # shorter lines are too generic to search for
_TOKEN = re.compile(r"[\w.\-]+")


def _norm(s: str) -> str:
    return " ".join(unicodedata.normalize("NFC", s).split())


def _words(s: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFKC", s).casefold())


def _grams(words: list[str], n: int) -> set[str]:
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


class Needles:
    """Closed ids and hashes (matched as tokens) and closed text (8-word runs, and short lines)."""

    def __init__(self):
        self.tokens: dict[str, str] = {}  # casefolded token -> what it is
        self.runs: set[str] = set()
        self.short: set[str] = set()

    def add_text(self, text: str, short_ok: bool = True) -> None:
        for line in text.splitlines():
            w = _words(line)
            if len(w) >= SHINGLE:
                self.runs |= _grams(w, SHINGLE)
            elif short_ok and SHORT[0] <= len(w) <= SHORT[1] and len(_norm(line)) >= MIN_CHARS:
                self.short.add(" ".join(w))

    def drop(self, other: "Needles") -> None:
        self.runs -= other.runs
        self.short -= other.short

    def __bool__(self) -> bool:
        return bool(self.tokens or self.runs or self.short)

    def find(self, strings) -> str | None:
        lengths = sorted({s.count(" ") + 1 for s in self.short})
        for s in strings:
            for t in _TOKEN.findall(unicodedata.normalize("NFC", s).casefold()):
                for x in (t, t.strip(".-")):  # a token can end a sentence
                    if x in self.tokens:
                        return self.tokens[x]
            w = _words(s)
            if self.runs and len(w) >= SHINGLE and not self.runs.isdisjoint(_grams(w, SHINGLE)):
                return "closed label or output text"
            if any(not self.short.isdisjoint(_grams(w, n)) for n in lengths if n <= len(w)):
                return "closed label, output or title text"
        return None


def _outputs(track: str):
    d = run_dir(track)
    return d.rglob("page-*.md") if d.exists() else []


def _corpus_text(track: str, n: Needles) -> list:
    docs = load_documents(track)
    for d in docs:
        for p in page_statuses(d):
            n.add_text((load_page(d, p) or {}).get("markdown") or "")
    for f in _outputs(track) if docs else []:
        n.add_text(f.read_text(encoding="utf-8", errors="replace"))
    return docs


def _closed_needles() -> Needles:
    """Everything from the closed track that must never appear. Empty without one on this machine."""
    n = Needles()
    docs = _corpus_text("closed", n)
    if not docs:
        return n
    for d in docs:
        for what, tok in (("closed document id", d.document_id), ("closed PDF hash", d.sha256)):
            if tok:
                n.tokens[unicodedata.normalize("NFC", tok).casefold()] = what
        if d.title and len(_words(d.title)) >= SHORT[0]:
            n.add_text(d.title)
    seen_open = Needles()
    _corpus_text("open", seen_open)
    n.drop(seen_open)  # boilerplate shared with open pages is not a leak
    return n


def _published_closed() -> dict[str, dict]:
    """system -> the closed summary export-closed published for it."""
    out, d = {}, published_dir("closed")
    for f in sorted(d.glob("*.json")) if d.exists() else []:
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if isinstance(s, dict):
            out[str(s.get("system") or f.stem)] = s
    return out


def _pages(res: dict) -> int:
    c = res.get("counts")
    try:
        return int((c if isinstance(c, dict) else {}).get("pages") or 0)
    except (TypeError, ValueError):
        return 0


def _closed_problem(where: str, res: dict, system, published: dict) -> str | None:
    pub = published.get(str(system)) if system is not None else None
    scores = res.get("scores", {"overall": res.get("overall")} if "overall" in res else None)
    if (pub is None or not pub.get("publishable") or _pages(pub) < MIN_CLOSED_PAGES
            or not res.get("run_id") or res.get("run_id") != pub.get("run_id")
            or _pages(res) != _pages(pub)
            or (scores != pub.get("scores") and scores != {"overall": (pub.get("scores") or {}).get("overall")})):
        return (f"{where}: a closed-track result for {system!r} that is not exactly what export-closed published "
                f"(same run, scores and page count, publishable, {MIN_CLOSED_PAGES} or more pages)")
    return None


def _nodes(obj, path="", key=None, parent=None):
    """Every value in a JSON document, the root included: (path, key it sits under, value, parent dict).
    List items keep the key of their list."""
    yield path, key, obj, parent
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _nodes(v, f"{path}.{k}", k, obj)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _nodes(v, f"{path}[{i}]", key, parent)


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def check(folder: Path) -> list[str]:
    """Problems found in an exported site folder. An empty list means it is safe to publish."""
    folder = Path(folder)
    api = folder / "api"
    if not api.is_dir():
        return [f"{folder} has no api/ folder: run `bambench export-site {folder}` first"]
    problems = [f"api/{n}.json is missing: {folder} is not a complete export" for n in sorted(API_FILES)
                if not (api / f"{n}.json").is_file()]
    open_docs = load_documents("open")
    open_ids, open_families = {d.document_id for d in open_docs}, {d.family_id for d in open_docs}
    site_files = {f.name for f in SITE.iterdir() if f.is_file() and f.suffix in SITE_SUFFIXES} | {"config.js"}
    published = _published_closed()
    try:
        board = json.loads((api / "leaderboard.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        board = []
    open_systems = {r.get("system") for r in board if isinstance(r, dict) and r.get("open")} if isinstance(board, list) else set()
    texts = {}  # rel -> strings, for the closed-corpus search
    for f in sorted(p for p in folder.rglob("*") if p.is_file()):
        rel = f.relative_to(folder).as_posix()
        pair = VERSUS.fullmatch(rel)
        known = ("/" not in rel and rel in site_files) or (rel.startswith("api/") and rel[4:-5] in API_FILES
                                                            and rel.endswith(".json") and rel.count("/") == 1)
        if pair and not (pair[1] in open_systems and pair[2] in open_systems and pair[1] < pair[2]):
            problems.append(f"{rel}: a pair file for systems that are not both open-track systems on the leaderboard")
            continue
        if not (known or pair):
            problems.append(f"{rel}: export-site never writes this file, so it has no place in a hosted copy")
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        if not rel.endswith(".json"):
            texts[rel] = [rel, text]
            continue
        try:
            data = json.loads(text)
        except ValueError:
            problems.append(f"{rel}: not valid JSON")
            continue
        texts[rel] = [rel, *_strings(data)]
        for path, k, node, parent in _nodes(data):
            where = f"{rel} at {path or '/'}"
            if k in DOC_KEYS and not isinstance(node, (dict, list)):
                if not isinstance(node, str) or node not in (open_families if k == "family_id" else open_ids):
                    problems.append(f"{where}: {k} {node!r} is not an open-track document")
            if k in TEXT_KEYS and node and path.endswith(f".{k}"):
                problems.append(f"{where}: {k!r} holds page text or model output")
            if not (isinstance(node, dict) and ("scores" in node or "overall" in node)
                    and (node.get("track") == "closed" or "closed" in str(k or "").lower())):
                continue
            if "pages" in node and not {"system", "run_id", "card", "counts"} & node.keys():
                # An aggregate such as label agreement: published only when cleared and backed by enough pages.
                try:
                    enough = int(node.get("pages") or 0) >= MIN_CLOSED_PAGES
                except (TypeError, ValueError):
                    enough = False
                if not (node.get("publishable") is True and enough):
                    problems.append(f"{where}: a closed-track figure on fewer than {MIN_CLOSED_PAGES} pages or not cleared")
                continue
            system = node.get("system", (parent or {}).get("system") if k == "closed" else None)
            if (pr := _closed_problem(where, node, system, published)):
                problems.append(pr)
    needles = _closed_needles()
    if needles:
        for rel, strings in texts.items():
            if (hit := needles.find(strings)):
                problems.append(f"{rel}: contains {hit}")
    return problems
