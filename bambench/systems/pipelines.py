"""Two-stage document parsers whose vision model is served by vLLM on this machine.

PaddleOCR-VL, GLM-OCR and MinerU2.5-Pro first find the layout blocks on a page and then read
each block with their VLM. Their own client code does both steps; we point it at the local vLLM
server, so the same local-only rule applies as for single-call models.

The PaddleOCR and GLM-OCR clients run as command-line tools, so they can live in their own
virtual environment (card key `cli`) and never clash with vLLM's dependencies. They run with a
dead proxy for every host except this machine, so a wrong setting can only fail, never upload.
The layout models must be downloaded on the login node first, because compute nodes have no
internet.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

from ..corpus import Document, page_image
from .base import Progress
from .vllm_vlm import VllmVlm, allowed_host

LOCAL_ONLY_ENV = {
    "http_proxy": "http://127.0.0.1:9", "https_proxy": "http://127.0.0.1:9",
    "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",
    "no_proxy": "127.0.0.1,localhost", "NO_PROXY": "127.0.0.1,localhost",
    "HF_HUB_OFFLINE": "1", "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK": "True",
}


class _CliPipeline(VllmVlm):
    """A parser run as a command per page image; reads the Markdown files it writes."""

    command = ""
    install = ""

    def cli(self) -> str | None:
        path = self.card.get("cli")
        if path:
            path = os.path.expanduser(path)
            return path if os.access(path, os.X_OK) else None
        return shutil.which(self.command)

    def available(self) -> tuple[bool, str]:
        if not self.cli():
            return False, f"{self.card.get('cli') or self.command} is not installed ({self.install})"
        return super().available()

    def args(self, image: str, out_dir: str) -> list[str]:
        raise NotImplementedError

    def predict(self, doc: Document, pages: list[int], progress: Progress) -> dict:
        if not allowed_host(self.base_url):
            raise PermissionError(f"Refusing to send document pages to {self.base_url}")
        env = {**os.environ, **LOCAL_ONLY_ENV}
        out = {}
        for p in pages:
            t = time.time()
            with tempfile.TemporaryDirectory() as d:
                image = str(page_image(doc, p, self.card.get("dpi", 144)))
                r = subprocess.run([self.cli(), *self.args(image, d)], capture_output=True, text=True, env=env,
                                   timeout=self.card.get("timeout_s", 600))
                if r.returncode:
                    raise RuntimeError(f"{self.command} failed on page {p}: {(r.stderr or r.stdout)[-2000:]}")
                mds = sorted(Path(d).rglob("*.md"))
                out[p] = "\n\n".join(f.read_text(encoding="utf-8") for f in mds).strip()
            progress(f"page {p} in {time.time() - t:.1f}s")
        return {"pages": out, "records": None}


class PaddleOcrVl(_CliPipeline):
    """`paddleocr doc_parser` (PP-DocLayout + PaddleOCR-VL) with the VLM on the local vLLM server."""

    kind = "paddleocr_vl"
    command = "paddleocr"
    install = 'pip install "paddleocr[doc-parser]>=3.4.0" paddlepaddle'

    def args(self, image: str, out_dir: str) -> list[str]:
        return ["doc_parser", "-i", image, "--pipeline_version", self.card.get("pipeline_version", "v1.6"),
                "--vl_rec_backend", "vllm-server", "--vl_rec_server_url", self.base_url, "--save_path", out_dir]


class GlmOcr(_CliPipeline):
    """GLM-OCR's own SDK: PP-DocLayoutV3 finds the blocks, GLM-OCR on the local vLLM server reads each."""

    kind = "glm_ocr"
    command = "glmocr"
    install = 'pip install "glmocr[selfhosted]"'

    def args(self, image: str, out_dir: str) -> list[str]:
        url = urlparse(self.base_url)
        return ["parse", image, "--output", out_dir, "--layout-device", self.card.get("layout_device", "cpu"),
                # MaaS mode would send the page to Zhipu's cloud API; self-hosted mode only.
                "--set", "pipeline.maas.enabled", "false",
                "--set", "pipeline.ocr_api.api_host", url.hostname,
                "--set", "pipeline.ocr_api.api_port", str(url.port or 80),
                "--set", "pipeline.ocr_api.model", self.served_name]


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
