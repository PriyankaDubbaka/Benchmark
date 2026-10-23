"""Two-stage document parsers whose vision model is served by vLLM on this machine.

PaddleOCR-VL 1.6 and MinerU2.5-Pro first find the layout blocks on a page and then read each
block with their VLM. Their own client code does both steps; we point it at the local vLLM
server, so the same local-only rule applies as for single-call models.

Neither has been run on BAM hardware yet. The layout models these packages use must be
downloaded on the login node first, because compute nodes have no internet.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from ..corpus import Document, page_image
from .base import Progress
from .vllm_vlm import VllmVlm, allowed_host


class PaddleOcrVl(VllmVlm):
    """`paddleocr doc_parser` (PP-DocLayout + PaddleOCR-VL) with the VLM on the local vLLM server."""

    kind = "paddleocr_vl"

    def available(self) -> tuple[bool, str]:
        if not shutil.which("paddleocr"):
            return False, 'paddleocr is not installed (pip install "paddleocr[doc-parser]>=3.6.0" paddlepaddle)'
        return super().available()

    def predict(self, doc: Document, pages: list[int], progress: Progress) -> dict:
        if not allowed_host(self.base_url):
            raise PermissionError(f"Refusing to send document pages to {self.base_url}")
        out = {}
        for p in pages:
            t = time.time()
            with tempfile.TemporaryDirectory() as d:
                cmd = ["paddleocr", "doc_parser", "-i", str(page_image(doc, p, self.card.get("dpi", 144))),
                       "--pipeline_version", self.card.get("pipeline_version", "v1.6"),
                       "--vl_rec_backend", "vllm-server", "--vl_rec_server_url", self.base_url,
                       "--save_path", d]
                subprocess.run(cmd, check=True, capture_output=True, timeout=self.card.get("timeout_s", 600))
                mds = sorted(Path(d).rglob("*.md"))
                out[p] = "\n\n".join(f.read_text(encoding="utf-8") for f in mds).strip()
            progress(f"page {p} in {time.time() - t:.1f}s")
        return {"pages": out, "records": None}


class MineruVl(VllmVlm):
    """mineru-vl-utils two-step extraction (layout, then each block) against the local vLLM server."""

    kind = "mineru_vl"

    def available(self) -> tuple[bool, str]:
        try:
            import mineru_vl_utils  # noqa: F401
        except ImportError:
            return False, 'mineru-vl-utils is not installed (pip install "mineru-vl-utils[vllm]")'
        return super().available()

    def predict(self, doc: Document, pages: list[int], progress: Progress) -> dict:
        from mineru_vl_utils import MinerUClient
        from PIL import Image

        if not allowed_host(self.base_url):
            raise PermissionError(f"Refusing to send document pages to {self.base_url}")
        client = MinerUClient(backend="http-client", server_url=self.base_url.removesuffix("/v1"))
        out = {}
        for p in pages:
            t = time.time()
            blocks = client.two_step_extract(Image.open(page_image(doc, p, self.card.get("dpi", 144))))
            out[p] = self._blocks_to_markdown(blocks)
            progress(f"page {p} in {time.time() - t:.1f}s")
        return {"pages": out, "records": None}

    @staticmethod
    def _blocks_to_markdown(blocks) -> str:
        try:
            from mineru_vl_utils.post_process import json2md
            return json2md(blocks)
        except (ImportError, TypeError):
            pass
        drop = {"header", "footer", "page_number", "image"}
        parts = []
        for b in blocks or []:
            kind = (b.get("type") if isinstance(b, dict) else getattr(b, "type", "")) or ""
            text = (b.get("content") if isinstance(b, dict) else getattr(b, "content", "")) or ""
            if kind in drop or not str(text).strip():
                continue
            text = str(text).strip()
            if kind == "equation" and not text.startswith("$$"):
                text = "$$\n" + text.strip("$ \n") + "\n$$"
            parts.append(text)
        return "\n\n".join(parts)
