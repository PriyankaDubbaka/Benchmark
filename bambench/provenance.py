"""Facts about the software and weights behind a run, recorded in its summary.

Versions come from package metadata and are never imported, so asking is instant and cannot
start a GPU runtime.
"""
from __future__ import annotations

from importlib import metadata

from .models import _hf_homes

PACKAGES = ("vllm", "torch", "transformers", "tokenizers", "docling", "mineru", "paddleocr",
            "bitsandbytes", "accelerate", "pillow", "huggingface_hub")


def packages() -> dict[str, str]:
    """{name: version} of the packages above that are installed."""
    out = {}
    for name in PACKAGES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return out


def weights_revision(repo: str | None) -> str | None:
    """Commit hash of the local Hugging Face snapshot of a repo id such as "org/name", or None."""
    if not repo or "/" not in repo:
        return None
    for home in _hf_homes():
        folder = home / "hub" / ("models--" + repo.replace("/", "--"))
        ref = folder / "refs" / "main"
        try:
            if ref.is_file() and ref.read_text(encoding="utf-8").strip():
                return ref.read_text(encoding="utf-8").strip()
            snaps = [p.name for p in (folder / "snapshots").iterdir() if p.is_dir()]
        except OSError:
            continue
        if len(snaps) == 1:
            return snaps[0]
    return None
