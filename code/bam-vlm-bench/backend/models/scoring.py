from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class FieldAccuracy(BaseModel):
    value: float = 0.0
    unit: float = 0.0
    expanded_uncertainty: float = 0.0
    coverage_factor: float = 0.0
    status: float = 0.0
    oxide_formula: float = 0.0
    oxide_value: float = 0.0
    source_page: float = 0.0

class ExtractionScores(BaseModel):
    gold_records: int
    predicted_records: int
    exact_records: int
    record_precision: float
    record_recall: float
    record_f1: float
    field_accuracy: FieldAccuracy
    extra_elements: List[str] = []
    errors: List[Dict[str, Any]] = []

class RetrievalMetrics(BaseModel):
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    mrr_at_1: float = 0.0
    mrr_at_3: float = 0.0
    mrr_at_5: float = 0.0
    ndcg_at_1: float = 0.0
    ndcg_at_3: float = 0.0
    ndcg_at_5: float = 0.0
    complete_evidence_at_1: float = 0.0
    complete_evidence_at_3: float = 0.0
    complete_evidence_at_5: float = 0.0

class PerQueryResult(BaseModel):
    id: str
    category: str
    ranking: List[int]
    metrics: RetrievalMetrics

class RetrievalScores(BaseModel):
    query_count: int
    submitted_queries: int
    aggregate: RetrievalMetrics
    by_category: Dict[str, RetrievalMetrics] = {}
    per_query: List[PerQueryResult] = []

class BenchmarkResult(BaseModel):
    run_id: str
    model_id: str
    model_name: str
    provider: str
    document_id: str
    timestamp: str
    extraction_scores: Optional[ExtractionScores] = None
    retrieval_scores: Optional[RetrievalScores] = None
    timing_ms: float = 0
    cost_usd: float = 0.0
