from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Literal
from datetime import datetime

class ExtractionRecord(BaseModel):
    """A single extracted measurement from a certificate."""
    element: str = Field(..., pattern=r'^[A-Z][a-z]?$', description='Chemical element symbol')
    value: str = Field(..., description='Decimal string value')
    unit: Literal['%', 'mg/kg'] = Field(..., description='Measurement unit')
    expanded_uncertainty: str = Field(..., description='Expanded uncertainty as decimal string')
    coverage_factor: int = Field(default=2, gt=0, description='Coverage factor k')
    status: Literal['certified', 'information_only'] = Field(..., description='Certification status')
    oxide_formula: Optional[str] = Field(None, description='Oxide formula e.g. Al2O3')
    oxide_value: Optional[str] = Field(None, description='Oxide value as decimal string')
    source_page: int = Field(..., ge=1, description='1-indexed PDF page number')

class RetrievalQuery(BaseModel):
    """A retrieval question with expected answer and evidence."""
    id: str
    query: str
    category: Literal['table_lookup', 'qualification', 'cross_page', 'provenance', 'usage', 'method']
    expected_answer: str
    evidence_pages: List[int]
    relevance: Dict[str, int]  # page number string -> relevance score (0/1/2)

class DocumentMetadata(BaseModel):
    """Document identity and provenance."""
    document_id: str
    filename: str
    sha256: str
    page_count: int
    language: str = 'en'
    source_url: Optional[str] = None
    document_version: Optional[str] = None
    accepted_date: Optional[str] = None
    revision_date: Optional[str] = None

class DocumentAnnotation(BaseModel):
    """Complete gold-standard master copy annotation for one document."""
    schema_version: str = '1.0'
    document_id: str
    annotation_status: Literal['expert_validated', 'machine_assisted_draft', 'template_only']
    scope: str
    extraction_records: List[ExtractionRecord]
    retrieval_queries: List[RetrievalQuery]
    metadata: DocumentMetadata
    notes: Optional[str] = None
