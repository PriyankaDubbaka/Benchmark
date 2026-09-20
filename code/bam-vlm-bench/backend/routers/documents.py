import os
import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

router = APIRouter()

def _find_dataset_dir() -> Path:
    # Try various relative and absolute candidate paths
    candidates = [
        Path(os.environ.get('PDF_DIR', '')),
        Path(__file__).resolve().parent.parent.parent.parent / 'dataset',
        Path(__file__).resolve().parent.parent / 'data' / 'dataset',
        Path("c:/Users/pdubbaka/OneDrive - Bundesanstalt für Materialforschung und -prüfung (BAM)/Desktop/Benchmarks/dataset")
    ]
    for c in candidates:
        if c and c.exists() and c.is_dir():
            return c
    # Fallback to creating local folder
    fallback = Path(__file__).resolve().parent.parent.parent / 'dataset'
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

def _get_annotations_dir() -> Path:
    return Path(__file__).resolve().parent.parent / 'data' / 'annotations'

DOCUMENTS_REGISTRY = [
    {
        "id": "bam-s005c-v2",
        "filename": "Zertifikat_BAM-S005c_rev1.pdf",
        "title": "BAM-S005c V2 (Glass Reference Material)",
        "default_pages": 8,
        "annotation_file": "bam-s005c-v2.json"
    },
    {
        "id": "bam-d001",
        "filename": "BAM-D001_Certificate_en.pdf",
        "title": "BAM-D001 Certificate",
        "default_pages": 4,
        "annotation_file": "bam-d001.json"
    },
    {
        "id": "bam-k009a",
        "filename": "Certificate_BAM-K009a_webshop.pdf",
        "title": "BAM-K009a Webshop Certificate",
        "default_pages": 4,
        "annotation_file": "bam-k009a.json"
    },
    {
        "id": "bam-k001",
        "filename": "Certificate_K001.pdf",
        "title": "BAM-K001 Certificate",
        "default_pages": 4,
        "annotation_file": "bam-k001.json"
    },
    {
        "id": "bam-u130",
        "filename": "Zertifikat_BAM-U130_en_V2_web.pdf",
        "title": "BAM-U130 V2 Certificate",
        "default_pages": 4,
        "annotation_file": "bam-u130.json"
    }
]

@router.get('/documents')
def list_documents():
    """List all available PDF certificates and their master copy annotation status."""
    dataset_dir = _find_dataset_dir()
    annotations_dir = _get_annotations_dir()
    
    docs_out = []
    for entry in DOCUMENTS_REGISTRY:
        doc_id = entry["id"]
        pdf_path = dataset_dir / entry["filename"]
        ann_path = annotations_dir / entry["annotation_file"]
        
        has_file = pdf_path.exists()
        has_ann = ann_path.exists()
        
        ann_status = "unannotated"
        rec_count = 0
        q_count = 0
        page_count = entry["default_pages"]
        
        if has_ann:
            try:
                with open(ann_path, 'r', encoding='utf-8') as f:
                    ann_data = json.load(f)
                    ann_status = ann_data.get('annotation_status', 'template_only')
                    rec_count = len(ann_data.get('extraction_records', []))
                    q_count = len(ann_data.get('retrieval_queries', []))
                    if 'metadata' in ann_data and 'page_count' in ann_data['metadata']:
                        page_count = ann_data['metadata']['page_count']
            except Exception:
                pass
                
        docs_out.append({
            "id": doc_id,
            "filename": entry["filename"],
            "title": entry["title"],
            "pageCount": page_count,
            "page_count": page_count,
            "hasAnnotation": has_ann and rec_count > 0,
            "has_annotation": has_ann and rec_count > 0,
            "annotationStatus": ann_status,
            "annotation_status": ann_status,
            "extractionRecordsCount": rec_count,
            "retrievalQueriesCount": q_count,
            "existsOnDisk": has_file
        })
    return docs_out

@router.get('/documents/{doc_id}/annotation')
def get_annotation(doc_id: str):
    """Get the ground truth master copy annotation for a given document."""
    entry = next((d for d in DOCUMENTS_REGISTRY if d["id"] == doc_id or d["filename"] == doc_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found in registry")
        
    ann_path = _get_annotations_dir() / entry["annotation_file"]
    if not ann_path.exists():
        raise HTTPException(status_code=404, detail=f"Annotation for '{doc_id}' does not exist")
        
    with open(ann_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@router.get('/documents/{doc_id}/pages')
def get_pages(doc_id: str):
    """Get page count and page index list for a document."""
    entry = next((d for d in DOCUMENTS_REGISTRY if d["id"] == doc_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
        
    page_count = entry["default_pages"]
    ann_path = _get_annotations_dir() / entry["annotation_file"]
    if ann_path.exists():
        try:
            with open(ann_path, 'r', encoding='utf-8') as f:
                d = json.load(f)
                page_count = d.get('metadata', {}).get('page_count', page_count)
        except Exception:
            pass
            
    return [{
        "pageNumber": i,
        "label": f"Page {i}",
        "thumbnailUrl": None
    } for i in range(1, page_count + 1)]

@router.post('/documents/upload')
async def upload_document(file: UploadFile = File(...)):
    """Upload a new certificate PDF to the dataset directory."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    dataset_dir = _find_dataset_dir()
    target_path = dataset_dir / file.filename
    
    contents = await file.read()
    with open(target_path, 'wb') as f:
        f.write(contents)
        
    return {
        "status": "ok",
        "filename": file.filename,
        "bytes": len(contents),
        "message": f"Saved to {target_path}"
    }
