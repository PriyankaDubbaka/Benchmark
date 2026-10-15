"""Docling pipeline baseline (layout model + TableFormer). Optional: pip install docling."""
from __future__ import annotations

from ..corpus import Document
from .base import Progress, System


class DoclingSystem(System):
    kind = "docling"

    def available(self) -> tuple[bool, str]:
        try:
            import docling  # noqa: F401
        except ImportError:
            return False, "docling is not installed (pip install docling)"
        return True, ""

    def predict(self, doc: Document, pages: list[int], progress: Progress) -> dict:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        opts = PdfPipelineOptions(do_ocr=self.card.get("ocr", False), do_table_structure=True)
        conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
        progress("converting with docling")
        result = conv.convert(str(doc.pdf_path)).document
        out = {}
        for p in pages:
            out[p] = result.export_to_markdown(page_no=p)
            progress(f"page {p}")
        return {"pages": out, "records": None}
