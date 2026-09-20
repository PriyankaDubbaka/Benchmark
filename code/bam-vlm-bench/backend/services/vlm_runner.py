import json
import re
from typing import List, Optional
from ..models.annotations import ExtractionRecord
from ..models.predictions import ModelPrediction, RawResponse, RetrievalRanking
from .providers.base import VLMProvider

EXTRACTION_PROMPT = """You are analyzing a BAM (Bundesanstalt für Materialforschung und -prüfung) certificate page.
Extract ALL elemental mass-fraction measurement records visible in the summary table(s) on this page.

For each element, extract:
- element: Chemical symbol (e.g. "Al", "Si", "Fe")
- value: The mass fraction value as a decimal string
- unit: Either "%" or "mg/kg"
- expanded_uncertainty: The expanded uncertainty value as decimal string
- coverage_factor: The coverage factor k (usually 2)
- status: "certified" or "information_only"
- oxide_formula: The oxide formula if shown (e.g. "Al2O3"), or null
- oxide_value: The oxide value if shown, or null

Return ONLY valid JSON array of objects. Example:
[{"element": "Al", "value": "0.587", "unit": "%", "expanded_uncertainty": "0.018", "coverage_factor": 2, "status": "certified", "oxide_formula": "Al2O3", "oxide_value": "1.109"}]

If no measurement table is found on this page, return an empty array: []
"""

RETRIEVAL_PROMPT_TEMPLATE = """You are analyzing a page from a BAM certificate document.
Does this page contain information relevant to answering the following question?

Question: {query}

Respond with a JSON object:
{{"relevant": true/false, "confidence": 0.0-1.0, "evidence_snippet": "brief quote if relevant"}}
"""

class VLMRunner:
    async def run_extraction(self, provider: VLMProvider, model_id: str, page_images: List[str]) -> List[dict]:
        """Run extraction on all pages, return raw responses."""
        results = []
        for i, img_path in enumerate(page_images, 1):
            try:
                resp = await provider.extract_from_page(model_id, img_path, EXTRACTION_PROMPT)
                results.append({
                    'page': i,
                    'response': resp['content'],
                    'tokens_in': resp['tokens_in'],
                    'tokens_out': resp['tokens_out'],
                    'latency_ms': resp['latency_ms']
                })
            except Exception as e:
                results.append({'page': i, 'response': '', 'error': str(e), 'tokens_in': 0, 'tokens_out': 0, 'latency_ms': 0})
        return results
    
    def parse_extraction_response(self, raw_responses: List[dict]) -> List[ExtractionRecord]:
        """Parse VLM responses into ExtractionRecord objects."""
        records = []
        for resp in raw_responses:
            content = resp.get('response', '')
            page = resp.get('page', 0)
            try:
                # Try to extract JSON from the response
                json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                if json_match:
                    items = json.loads(json_match.group())
                    for item in items:
                        item['source_page'] = page
                        try:
                            record = ExtractionRecord(**item)
                            records.append(record)
                        except Exception:
                            continue
            except (json.JSONDecodeError, Exception):
                continue
        return records
    
    async def run_retrieval(self, provider: VLMProvider, model_id: str, page_images: List[str], queries: List[dict]) -> List[RetrievalRanking]:
        """Rank pages by relevance for each query."""
        rankings = []
        for q in queries:
            page_scores = []
            prompt = RETRIEVAL_PROMPT_TEMPLATE.format(query=q['query'])
            for i, img_path in enumerate(page_images, 1):
                try:
                    resp = await provider.extract_from_page(model_id, img_path, prompt)
                    content = resp['content']
                    # Parse relevance
                    json_match = re.search(r'\{.*?\}', content, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        if data.get('relevant', False):
                            score = data.get('confidence', 0.5)
                            page_scores.append((i, score))
                except Exception:
                    continue
            # Sort by confidence descending
            page_scores.sort(key=lambda x: x[1], reverse=True)
            rankings.append(RetrievalRanking(
                query_id=q['id'],
                pages=[p for p, s in page_scores]
            ))
        return rankings
