"""Leak check for a hosted copy of the dashboard.

Run it after `bambench export-site public` and before the folder is published. It fails when the
folder holds anything that has to stay inside BAM, as far as a check of the folder can tell:

- any file export-site does not write: only the site's .html/.js/.css files, config.js, the fixed
  api/*.json files and pair files named after two open-track systems on the leaderboard
- a missing api file, so an empty or half-written folder never passes
- a document id that is not in the open track, as a value or inside a list
- page text, page items or raw model outputs, which a hosted copy never carries
- closed-track data anywhere other than the slots export-site fills, or different from what may be
  published: a leaderboard row's closed result must equal the summary export-closed published (and
  that summary must be publishable with 20 or more pages); the closed page counts, composition and
  agreement must equal what `closed_progress` gives; per-system closed flags only for those systems
- a file that cannot be read or checked, which counts as unsafe rather than passing

Where the closed track is present on the machine (the BAM cluster or a VDI), it also reads every
closed label and closed model output and searches every string in the folder, and every file path,
for closed document ids and hashes (as whole tokens), and for closed text: any run of 8 words, or a
whole closed line or title of 3 to 7 words and 20 or more characters, even inside a longer string.
Ids and text that also occur in files tracked by Git or in open-track pages and model outputs are
public already and are ignored, so boilerplate or a shared name does not block a clean export. A file
it cannot read while building or subtracting these lists is reported, never skipped. Text is held as 64-bit hashes,
model outputs are read only for pages without a label, and the exported files are checked one at a
time, so memory grows with about one copy of the closed text (some 15 MB per 1,000 pages).

What it cannot do: in CI the closed corpus is absent, so free text that is not marked as closed
cannot be recognised there. The protection in CI is that closed files never enter the repository
(the pre-commit guard and .gitignore). Run the check on the cluster or the VDI as well before
committing results; that is where the closed corpus is.
"""
from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from pathlib import Path

from . import runner
from .corpus import load_documents
from .gold import load_page, page_statuses
from .paths import ROOT, SITE, published_dir, run_dir

MIN_CLOSED_PAGES = runner.MIN_CLOSED_PAGES
SITE_SUFFIXES = {".html", ".js", ".css"}  # the only site files export-site copies
API_FILES = {"overview", "leaderboard", "models", "systems", "documents", "composition", "about"}
VERSUS = re.compile(r"api/versus/open/([^/]+)/([^/]+)\.json")
DOC_KEYS = {"document_id", "doc_id", "family_id"}  # values that name a document
TEXT_KEYS = {"page_items", "markdown", "prediction", "predictions"}  # page text or model output
SHINGLE = 8  # words in a run of closed text that counts as a match
SHORT = range(3, SHINGLE)  # word counts of whole short lines and titles that are matched too
MIN_CHARS = 20  # shorter lines are too generic to search for
PUBLIC_SUFFIXES = {".md", ".json", ".txt", ".yml", ".yaml", ".py", ".js", ".html", ".css", ".toml", ".cfg"}
_TOKEN = re.compile(r"[\w.\-]+")
DERIVED = {"cost", "scorer_current"}  # fields the leaderboard adds to a published summary when it reads it


def _words(s: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFKC", s).casefold())


def _grams(words: list[str], n: int):
    return (hash(" ".join(words[i:i + n])) for i in range(len(words) - n + 1))


class Needles:
    """Closed ids and hashes (matched as whole tokens) and closed text (hashed word runs)."""

    def __init__(self):
        self.tokens: dict[str, str] = {}  # casefolded token -> what it is
        self.runs: set[int] = set()  # hashes of 8-word runs
        self.short: set[int] = set()  # hashes of whole short lines and titles
        self.lengths: set[int] = set()  # word counts present in short

    def add_text(self, text: str) -> None:
        for line in text.splitlines():
            w = _words(line)
            if len(w) >= SHINGLE:
                self.runs.update(_grams(w, SHINGLE))
            elif len(w) in SHORT and len(" ".join(line.split())) >= MIN_CHARS:
                self.short.add(hash(" ".join(w)))
                self.lengths.add(len(w))

    def forget_public(self, text: str) -> None:
        """Drop every id, run and short phrase that also occurs, anywhere in a line, in public text."""
        if self.tokens:  # an id that is also an open system, document or any public word is not a leak
            for t in _TOKEN.findall(unicodedata.normalize("NFC", text).casefold()):
                for x in (t, t.strip(".-"), t.rsplit(".", 1)[0]):
                    self.tokens.pop(x, None)
        for line in text.splitlines():
            w = _words(line)
            if self.runs and len(w) >= SHINGLE:
                self.runs.difference_update(_grams(w, SHINGLE))
            for n in self.lengths:
                if self.short and len(w) >= n:
                    self.short.difference_update(_grams(w, n))

    def __bool__(self) -> bool:
        return bool(self.tokens or self.runs or self.short)

    def find(self, strings) -> str | None:
        for s in strings:
            for t in _TOKEN.findall(unicodedata.normalize("NFC", s).casefold()):
                for x in (t, t.strip(".-"), t.rsplit(".", 1)[0]):  # end of a sentence, or a file extension
                    if x in self.tokens:
                        return self.tokens[x]
            w = _words(s)
            if self.runs and len(w) >= SHINGLE and not self.runs.isdisjoint(_grams(w, SHINGLE)):
                return "closed label or output text"
            if any(not self.short.isdisjoint(_grams(w, n)) for n in self.lengths if n <= len(w)):
                return "closed label, output or title text"
        return None


def _outputs(track: str):
    d = run_dir(track)
    return d.rglob("page-*.md") if d.exists() else []


def _public_texts(problems: list[str]):
    """Text that is public already: files tracked by Git, open-track labels and model outputs.
    Anything that cannot be listed or read is reported in problems, never skipped silently."""
    try:
        names = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=True,
                               timeout=300).stdout.decode("utf-8", "surrogateescape").split("\0")
    except (OSError, subprocess.SubprocessError) as e:
        problems.append(f"could not list the files tracked by Git ({type(e).__name__}), so public text could not "
                        "be told apart from closed text; run the check inside the repository with git available")
        names = []
    for name in names:
        f = ROOT / name
        if name and not name.startswith("data/closed/") and f.suffix in PUBLIC_SUFFIXES and f.is_file():
            yield from _read(f, problems, "tracked file")
    for d in load_documents("open"):
        for p in page_statuses(d):
            yield (load_page(d, p) or {}).get("markdown") or ""
    for f in _outputs("open"):
        yield from _read(f, problems, "open-track output")


def _read(f: Path, problems: list[str], what: str):
    try:
        yield f.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        problems.append(f"could not read the {what} {f} ({type(e).__name__}); the check is incomplete")


def _closed_needles() -> tuple[Needles, list[str]]:
    """Everything from the closed track that must never appear, and any problem reading it. Empty
    without a closed track on this machine."""
    n, labelled, problems = Needles(), set(), []
    docs = load_documents("closed")
    if not docs:
        return n, problems
    for d in docs:
        for what, tok in (("closed document id", d.document_id), ("closed PDF hash", d.sha256)):
            if tok:
                n.tokens[unicodedata.normalize("NFC", tok).casefold()] = what
        if d.title and len(_words(d.title)) >= SHORT.start:
            n.add_text(d.title)
        for p in page_statuses(d):
            try:
                md = (load_page(d, p) or {}).get("markdown") or ""
            except (OSError, ValueError) as e:
                problems.append(f"could not read the closed label {d.document_id} page {p} ({type(e).__name__}); "
                                "the check is incomplete")
                continue
            if md.strip():
                labelled.add((d.document_id, p))
                n.add_text(md)
    # A model output transcribes the same page as its label, so a leaked output shares its 8-word runs
    # with the label. Outputs are read only for pages without a label, which keeps memory to about one
    # copy of the closed text however many systems ran.
    for f in _outputs("closed"):
        m = re.fullmatch(r"page-(\d+)\.md", f.name)
        if m and (f.parent.name, int(m[1])) not in labelled:
            for text in _read(f, problems, "closed output"):
                n.add_text(text)
    for text in _public_texts(problems):
        n.forget_public(text)
    return n, problems


def _published_closed() -> dict[str, dict]:
    """system -> the closed summary export-closed published for it, as the leaderboard reads it."""
    out, d = {}, published_dir("closed")
    for f in sorted(d.glob("*.json")) if d.exists() else []:
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(s, dict) and isinstance(s.get("system"), str):
            s.pop("page_items", None)
            out[s["system"]] = s
    return out


def _pages(res) -> int:
    c = res.get("counts") if isinstance(res, dict) else None
    try:
        return int((c if isinstance(c, dict) else {}).get("pages") or 0)
    except (TypeError, ValueError):
        return 0


def _closed_row_problem(where: str, res, system, published: dict) -> str | None:
    pub = published.get(system) if isinstance(system, str) else None
    ok = (pub is not None and pub.get("publishable") is True and _pages(pub) >= MIN_CLOSED_PAGES
          and isinstance(res, dict) and {k: v for k, v in res.items() if k not in DERIVED} == pub)
    return None if ok else (f"{where}: the closed-track result for {system!r} is not exactly what export-closed "
                            f"published, or that summary is not publishable with {MIN_CLOSED_PAGES} or more pages")


def _nodes(obj, path="", key=None):
    """Every value in a JSON document, the root included: (path, key, value). List items keep the
    key of their list."""
    yield path, key, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _nodes(v, f"{path}.{k}", k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _nodes(v, f"{path}[{i}]", key)


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _closed_slots(name: str, data, published: dict, progress) -> dict[str, str | None]:
    """The places where export-site puts closed-track data in this api file, each compared with its
    source: {path: problem, or None when it matches}."""
    slots: dict[str, str | None] = {}

    def same(path, value, expected, what):
        slots[path] = None if value == expected else \
            f"api/{name}.json at {path}: the closed {what} differs from what may be published"

    if name == "overview" and isinstance(data, dict):
        tracks, agree = data.get("tracks"), data.get("agreement")
        if isinstance(tracks, dict) and "closed" in tracks:
            same(".tracks.closed", tracks["closed"], progress, "page counts")
        if isinstance(agree, dict) and "closed" in agree:
            same(".agreement.closed", agree["closed"], (progress or {}).get("agreement"), "agreement")
    elif name == "composition" and isinstance(data, dict) and "closed" in data:
        same(".closed", data["closed"], (progress or {}).get("composition"), "composition")
    elif name == "leaderboard" and isinstance(data, list):
        for i, row in enumerate(data):
            if isinstance(row, dict) and row.get("closed") is not None:
                slots[f"[{i}].closed"] = _closed_row_problem(f"api/leaderboard.json at [{i}].closed", row["closed"],
                                                             row.get("system"), published)
    elif name == "models" and isinstance(data, dict) and isinstance(data.get("systems"), list):
        for i, s in enumerate(data["systems"]):
            if not isinstance(s, dict):
                continue
            cleared = isinstance(s.get("id"), str) and s["id"] in published
            rules = (("results", lambda v: v in (None, False) or (v is True and cleared)),
                     ("failure", lambda v: v is None),
                     ("seconds_per_page", lambda v: v is None or (cleared and type(v) in (int, float))))
            for field, fine in rules:
                d = s.get(field)
                if isinstance(d, dict) and "closed" in d:
                    p = f".systems[{i}].{field}.closed"
                    slots[p] = None if fine(d["closed"]) else \
                        f"api/models.json at {p}: closed-track data for a system export-closed has not published"
    return slots


def check(folder: Path) -> list[str]:
    """Problems found in an exported site folder. An empty list means it is safe to publish."""
    folder = Path(folder)
    api = folder / "api"
    if not api.is_dir():
        return [f"{folder} has no api/ folder: run `bambench export-site {folder}` first"]
    problems = [f"api/{n}.json is missing: {folder} is not a complete export" for n in sorted(API_FILES)
                if not (api / f"{n}.json").is_file()]
    open_docs = load_documents("open")
    ctx = {
        "open_ids": {d.document_id for d in open_docs}, "open_families": {d.family_id for d in open_docs},
        "site_files": {f.name for f in SITE.iterdir() if f.is_file() and f.suffix in SITE_SUFFIXES} | {"config.js"},
        "published": _published_closed(), "progress": None, "open_systems": set(),
    }
    try:
        ctx["progress"] = runner.closed_progress()
    except Exception as e:  # noqa: BLE001 - a broken closed folder must not let anything through unchecked
        problems.append(f"the closed-track counts could not be read ({type(e).__name__}); fix that first")
    try:
        board = json.loads((api / "leaderboard.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        board = []
    if isinstance(board, list):
        ctx["open_systems"] = {r["system"] for r in board if isinstance(r, dict)
                               and isinstance(r.get("system"), str) and r.get("open")}
    ctx["needles"], unreadable = _closed_needles()
    problems += unreadable
    for f in sorted(p for p in folder.rglob("*") if p.is_file()):
        rel = f.relative_to(folder).as_posix()
        try:
            problems += _check_file(f, rel, ctx)
        except Exception as e:  # noqa: BLE001 - whatever goes wrong, the file must not pass unchecked
            problems.append(f"{rel}: could not be checked ({type(e).__name__}: {e}); treat it as unsafe")
    return problems


def _check_file(f: Path, rel: str, ctx: dict) -> list[str]:
    pair = VERSUS.fullmatch(rel)
    known = ("/" not in rel and rel in ctx["site_files"]) or (rel.startswith("api/") and rel.count("/") == 1
                                                               and rel.endswith(".json") and rel[4:-5] in API_FILES)
    if pair and not (pair[1] in ctx["open_systems"] and pair[2] in ctx["open_systems"] and pair[1] < pair[2]):
        return [f"{rel}: a pair file for systems that are not both open-track systems on the leaderboard"]
    if not (known or pair):
        return [f"{rel}: export-site never writes this file, so it has no place in a hosted copy"]
    needles = ctx["needles"]
    text = f.read_text(encoding="utf-8", errors="replace")
    path_strings = [rel, *(Path(part).stem for part in rel.split("/"))]
    if not rel.endswith(".json"):
        hit = needles.find([*path_strings, text]) if needles else None
        return [f"{rel}: contains {hit}"] if hit else []
    try:
        data = json.loads(text)
    except ValueError:
        return [f"{rel}: not valid JSON"]
    slots = _closed_slots(rel[4:-5], data, ctx["published"], ctx["progress"]) if known else {}
    problems = [p for p in slots.values() if p]
    for path, k, node in _nodes(data):
        if any(path == s or path.startswith(s + ".") or path.startswith(s + "[") for s in slots):
            continue  # inside a closed slot, which was compared whole above
        where = f"{rel} at {path or '/'}"
        if k in DOC_KEYS and not isinstance(node, (dict, list)):
            if not isinstance(node, str) or node not in (ctx["open_families"] if k == "family_id" else ctx["open_ids"]):
                problems.append(f"{where}: {k} {node!r} is not an open-track document")
        if k in TEXT_KEYS and node and path.endswith(f".{k}"):
            problems.append(f"{where}: {k!r} holds page text or model output")
        closed_key = isinstance(k, str) and "closed" in k.lower() and path.endswith(f".{k}")
        if (closed_key and node not in (None, False)) or (isinstance(node, dict) and node.get("track") == "closed"):
            problems.append(f"{where}: closed-track data outside the places export-site fills")
    if needles and (hit := needles.find([*path_strings, *_strings(data)])):
        problems.append(f"{rel}: contains {hit}")
    return problems
