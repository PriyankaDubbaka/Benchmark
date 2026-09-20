from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from .annotations import ExtractionRecord

class RetrievalRanking(BaseModel):
    query_id: str
    pages: List[int]

class RawResponse(BaseModel):
    page: int
    prompt: str
    response: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0

class TimingInfo(BaseModel):
    total_ms: float
    pdf_conversion_ms: float = 0
    inference_ms: float = 0
    scoring_ms: float = 0

class CostInfo(BaseModel):
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    estimated_cost_usd: float = 0.0

class ModelPrediction(BaseModel):
    run_id: str
    model_id: str
    model_name: str
    provider: str
    document_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    extraction_records: List[ExtractionRecord] = []
    retrieval_rankings: List[RetrievalRanking] = []
    raw_responses: List[RawResponse] = []
    timing: TimingInfo
    cost: CostInfo = Field(default_factory=CostInfo)
    status: Literal['completed', 'failed', 'partial'] = 'completed'
    error: Optional[str] = None
