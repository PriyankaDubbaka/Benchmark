import uuid
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from ..models.annotations import DocumentAnnotation
from ..models.predictions import ModelPrediction, RawResponse, TimingInfo, CostInfo
from ..models.scoring import BenchmarkResult
from .pdf_processor import PDFProcessor
from .vlm_runner import VLMRunner
from .scorer import score_extraction, score_retrieval
from .providers.base import VLMProvider

# In-memory store for benchmark runs
_runs: Dict[str, dict] = {}

class BenchmarkService:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.vlm_runner = VLMRunner()
    
    async def run_benchmark(
        self,
        provider: VLMProvider,
        model_id: str,
        model_name: str,
        pdf_path: str,
        annotation: DocumentAnnotation,
        run_extraction: bool = True,
        run_retrieval: bool = True,
        progress_callback = None
    ) -> BenchmarkResult:
        run_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Update status
        _runs[run_id] = {'status': 'converting_pdf', 'progress': 0.1}
        
        # Convert PDF to images
        t0 = time.time()
        page_images = self.pdf_processor.convert_to_images(pdf_path)
        pdf_ms = (time.time() - t0) * 1000
        
        extraction_scores = None
        retrieval_scores = None
        raw_responses = []
        total_tokens_in = 0
        total_tokens_out = 0
        
        # Run extraction
        if run_extraction and annotation.extraction_records:
            _runs[run_id] = {'status': 'running_extraction', 'progress': 0.3}
            t0 = time.time()
            extraction_raw = await self.vlm_runner.run_extraction(provider, model_id, page_images)
            inference_ms = (time.time() - t0) * 1000
            
            for r in extraction_raw:
                raw_responses.append(RawResponse(
                    page=r['page'], prompt='extraction', response=r['response'],
                    tokens_in=r.get('tokens_in', 0), tokens_out=r.get('tokens_out', 0),
                    latency_ms=r.get('latency_ms', 0)
                ))
                total_tokens_in += r.get('tokens_in', 0)
                total_tokens_out += r.get('tokens_out', 0)
            
            pred_records = self.vlm_runner.parse_extraction_response(extraction_raw)
            extraction_scores = score_extraction(
                [r.model_dump() for r in annotation.extraction_records],
                [r.model_dump() for r in pred_records],
                annotation.metadata.page_count
            )
        
        # Run retrieval
        if run_retrieval and annotation.retrieval_queries:
            _runs[run_id] = {'status': 'running_retrieval', 'progress': 0.6}
            queries_data = [q.model_dump() for q in annotation.retrieval_queries]
            pred_rankings = await self.vlm_runner.run_retrieval(provider, model_id, page_images, queries_data)
            retrieval_scores = score_retrieval(
                queries_data,
                [r.model_dump() for r in pred_rankings],
                annotation.metadata.page_count
            )
        
        total_ms = (time.time() - start_time) * 1000
        _runs[run_id] = {'status': 'completed', 'progress': 1.0}
        
        result = BenchmarkResult(
            run_id=run_id,
            model_id=model_id,
            model_name=model_name,
            provider=provider.provider_id(),
            document_id=annotation.document_id,
            timestamp=datetime.utcnow().isoformat(),
            extraction_scores=extraction_scores,
            retrieval_scores=retrieval_scores,
            timing_ms=total_ms,
            cost_usd=0.0  # Would need pricing info per provider
        )
        
        # Save result to disk
        results_dir = Path('./results') / run_id
        results_dir.mkdir(parents=True, exist_ok=True)
        with open(results_dir / 'result.json', 'w') as f:
            f.write(result.model_dump_json(indent=2))
        
        return result
    
    def get_run_status(self, run_id: str) -> Optional[dict]:
        return _runs.get(run_id)
    
    def list_results(self) -> List[dict]:
        results_dir = Path('./results')
        if not results_dir.exists():
            return []
        results = []
        for run_dir in sorted(results_dir.iterdir()):
            result_file = run_dir / 'result.json'
            if result_file.exists():
                with open(result_file) as f:
                    results.append(json.loads(f.read()))
        return results
