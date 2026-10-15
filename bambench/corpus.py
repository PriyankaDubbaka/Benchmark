"""Documents, their PDFs, page text and page images.

A document is one JSON manifest in data/<track>/documents/. The manifest pins the PDF by
SHA-256 so labels are never scored against a different revision of the file.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from .paths import CACHE, ROOT, track_dir

DOC_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{1,80}$")


@dataclass
class Document:
    document_id: str
    track: str
    pdf: str
    sha256: str
    page_count: int
    title: str = ""
    doc_type: str = "certificate"
    family_id: str = ""
    department: str = ""
    language: str = "en"
    split: str = "dev"
    rights_status: str = "unverified"
    added: str = ""
    notes: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def pdf_path(self) -> Path:
        p = Path(self.pdf)
        return p if p.is_absolute() else ROOT / p

    def to_json(self) -> dict:
        d = asdict(self)
        d.pop("track")
        extra = d.pop("extra")
        return {**d, **{k: v for k, v in extra.items() if k not in d}}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _manifest_dir(track: str) -> Path:
    return track_dir(track) / "documents"


def load_documents(track: str) -> list[Document]:
    out = []
    d = _manifest_dir(track)
    if not d.exists():
        return out
    known = set(Document.__dataclass_fields__) - {"track", "extra"}
    for f in sorted(d.glob("*.json")):
        raw = json.loads(f.read_text(encoding="utf-8"))
        extra = {k: v for k, v in raw.items() if k not in known}
        kwargs = {k: v for k, v in raw.items() if k in known}
        out.append(Document(track=track, extra=extra, **kwargs))
    return out


def get_document(track: str, document_id: str) -> Document:
    for d in load_documents(track):
        if d.document_id == document_id:
            return d
    raise KeyError(f"No document {document_id!r} in the {track} track")


def verify(doc: Document) -> None:
    if not doc.pdf_path.exists():
        raise FileNotFoundError(f"{doc.document_id}: PDF missing at {doc.pdf_path}")
    actual = sha256_file(doc.pdf_path)
    if actual != doc.sha256:
        raise ValueError(
            f"{doc.document_id}: PDF checksum differs from the manifest. "
            "Do not score another revision against these labels."
        )


def pdf_page_count(path: Path) -> int:
    out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, check=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    if not m:
        raise ValueError(f"Could not read page count of {path}")
    return int(m.group(1))


def register(track: str, pdf: Path, document_id: str, copy_into_track: bool, **meta) -> Document:
    """Add a PDF to a track. Closed-track PDFs are copied into the gitignored closed folder."""
    if not DOC_ID.match(document_id):
        raise ValueError("document_id: lowercase letters, digits, dot, dash or underscore")
    if any(d.document_id == document_id for d in load_documents(track)):
        raise ValueError(f"{document_id} already exists in the {track} track")
    pdf = pdf.resolve()
    if copy_into_track:
        dest_dir = track_dir(track) / "pdfs"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{document_id}.pdf"
        shutil.copyfile(pdf, dest)
        pdf = dest
    try:
        rel = str(pdf.relative_to(ROOT))
    except ValueError:
        rel = str(pdf)
    doc = Document(
        document_id=document_id,
        track=track,
        pdf=rel,
        sha256=sha256_file(pdf),
        page_count=pdf_page_count(pdf),
        added=date.today().isoformat(),
        **{k: v for k, v in meta.items() if v is not None},
    )
    d = _manifest_dir(track)
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{document_id}.json").write_text(json.dumps(doc.to_json(), indent=2) + "\n", encoding="utf-8")
    return doc


def _cache(doc: Document) -> Path:
    # Closed-track caches live under the closed folder so page text and images never sit in .cache.
    base = track_dir("closed") / ".cache" if doc.track == "closed" else CACHE
    p = base / doc.document_id / doc.sha256[:12]
    p.mkdir(parents=True, exist_ok=True)
    return p


def page_texts(doc: Document) -> list[str]:
    """Poppler layout text, one string per page."""
    cache = _cache(doc) / "pdftotext.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    text = subprocess.run(
        ["pdftotext", "-layout", str(doc.pdf_path), "-"], capture_output=True, text=True, check=True
    ).stdout
    parts = text.split("\f")
    while parts and not parts[-1].strip():
        parts.pop()
    parts += [""] * (doc.page_count - len(parts))
    cache.write_text(json.dumps(parts[: doc.page_count]), encoding="utf-8")
    return parts[: doc.page_count]


def page_image(doc: Document, page: int, dpi: int = 110) -> Path:
    if not 1 <= page <= doc.page_count:
        raise ValueError(f"Page {page} out of range 1..{doc.page_count}")
    out = _cache(doc) / f"page-{page:03d}-{dpi}.png"
    if not out.exists():
        stem = out.with_suffix("")
        subprocess.run(
            ["pdftoppm", "-r", str(dpi), "-png", "-singlefile", "-f", str(page), "-l", str(page),
             str(doc.pdf_path), str(stem)],
            check=True, capture_output=True,
        )
    return out
