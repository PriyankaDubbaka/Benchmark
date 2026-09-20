import math
from typing import Dict, List, Any
from ..models.scoring import ExtractionScores, FieldAccuracy, RetrievalScores, RetrievalMetrics, PerQueryResult

def decimal_normalize(s: str) -> str:
    """Normalize decimal strings (strip trailing/leading zeros etc)"""
    if s is None:
        return s
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
        return str(f).rstrip('0').rstrip('.') if '.' in str(f) else str(f)
    except ValueError:
        return s.strip()

def validate_records(records, page_count):
    valid_records = []
    for r in records:
        if r.get('source_page', 0) > page_count:
            continue
        valid_records.append(r)
    return valid_records

def score_extraction(gold_records: List[Dict[str, Any]], pred_records: List[Dict[str, Any]], page_count: int) -> ExtractionScores:
    pred_records = validate_records(pred_records, page_count)
    gold_dict = {r['element']: r for r in gold_records}
    pred_dict = {r['element']: r for r in pred_records}
    
    exact_records = 0
    field_acc = FieldAccuracy()
    
    matched_elements = set(gold_dict.keys()).intersection(pred_dict.keys())
    
    for el in matched_elements:
        g = gold_dict[el]
        p = pred_dict[el]
        
        all_match = True
        
        fields_to_check = [
            'value', 'unit', 'expanded_uncertainty', 'coverage_factor',
            'status', 'oxide_formula', 'oxide_value', 'source_page'
        ]
        
        for field in fields_to_check:
            g_val = g.get(field)
            p_val = p.get(field)
            
            if field in ['value', 'expanded_uncertainty', 'oxide_value']:
                g_val = decimal_normalize(str(g_val)) if g_val is not None else None
                p_val = decimal_normalize(str(p_val)) if p_val is not None else None
            
            if str(g_val) == str(p_val):
                setattr(field_acc, field, getattr(field_acc, field) + 1)
            else:
                all_match = False
                
        if all_match:
            exact_records += 1
            
    extra_elements = list(set(pred_dict.keys()) - set(gold_dict.keys()))
    missing_elements = list(set(gold_dict.keys()) - set(pred_dict.keys()))
    
    gold_count = len(gold_records)
    pred_count = len(pred_records)
    
    precision = exact_records / pred_count if pred_count > 0 else 0.0
    recall = exact_records / gold_count if gold_count > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    if gold_count > 0:
        for field in field_acc.model_dump().keys():
            setattr(field_acc, field, getattr(field_acc, field) / gold_count)
            
    return ExtractionScores(
        gold_records=gold_count,
        predicted_records=pred_count,
        exact_records=exact_records,
        record_precision=precision,
        record_recall=recall,
        record_f1=f1,
        field_accuracy=field_acc,
        extra_elements=extra_elements,
        errors=[{'type': 'missing', 'element': e} for e in missing_elements]
    )

def _compute_ndcg(ranking: List[int], relevance: Dict[str, int], k: int) -> float:
    dcg = 0.0
    idcg = 0.0
    for i, page in enumerate(ranking[:k]):
        rel = relevance.get(str(page), 0)
        dcg += (2**rel - 1) / math.log2(i + 2)
        
    ideal_ranking = sorted([rel for rel in relevance.values() if rel > 0], reverse=True)
    for i, rel in enumerate(ideal_ranking[:k]):
        idcg += (2**rel - 1) / math.log2(i + 2)
        
    return dcg / idcg if idcg > 0 else 0.0

def score_retrieval(queries: List[Dict[str, Any]], pred_rankings: List[Dict[str, Any]], page_count: int) -> RetrievalScores:
    per_query = []
    
    for query, ranking_data in zip(queries, pred_rankings):
        ranking = ranking_data['pages']
        relevance = query.get('relevance', {})
        relevant_pages = set(int(k) for k, v in relevance.items() if v > 0)
        
        mrr_1 = mrr_3 = mrr_5 = 0.0
        recall_1 = recall_3 = recall_5 = 0.0
        ndcg_1 = ndcg_3 = ndcg_5 = 0.0
        complete_1 = complete_3 = complete_5 = 0.0
        
        for k in [1, 3, 5]:
            top_k = ranking[:k]
            hits = sum(1 for p in top_k if p in relevant_pages)
            
            if hits > 0:
                first_hit_idx = next(i for i, p in enumerate(top_k) if p in relevant_pages)
                if k == 1: mrr_1 = 1.0 / (first_hit_idx + 1)
                if k == 3: mrr_3 = 1.0 / (first_hit_idx + 1) if not mrr_3 else mrr_3
                if k == 5: mrr_5 = 1.0 / (first_hit_idx + 1) if not mrr_5 else mrr_5
                
            recall = hits / len(relevant_pages) if relevant_pages else 0.0
            if k == 1: recall_1 = recall
            if k == 3: recall_3 = recall
            if k == 5: recall_5 = recall
            
            ndcg = _compute_ndcg(ranking, relevance, k)
            if k == 1: ndcg_1 = ndcg
            if k == 3: ndcg_3 = ndcg
            if k == 5: ndcg_5 = ndcg
            
            complete = 1.0 if all(p in top_k for p in relevant_pages) else 0.0
            if k == 1: complete_1 = complete
            if k == 3: complete_3 = complete
            if k == 5: complete_5 = complete
            
        metrics = RetrievalMetrics(
            recall_at_1=recall_1, recall_at_3=recall_3, recall_at_5=recall_5,
            mrr_at_1=mrr_1, mrr_at_3=mrr_3, mrr_at_5=mrr_5,
            ndcg_at_1=ndcg_1, ndcg_at_3=ndcg_3, ndcg_at_5=ndcg_5,
            complete_evidence_at_1=complete_1, complete_evidence_at_3=complete_3, complete_evidence_at_5=complete_5
        )
        
        per_query.append(PerQueryResult(
            id=query['id'],
            category=query['category'],
            ranking=ranking,
            metrics=metrics
        ))
        
    def _agg(ms):
        if not ms: return RetrievalMetrics()
        agg = RetrievalMetrics()
        for f in agg.model_dump().keys():
            setattr(agg, f, sum(getattr(m.metrics, f) for m in ms) / len(ms))
        return agg

    return RetrievalScores(
        query_count=len(queries),
        submitted_queries=len(queries),
        aggregate=_agg(per_query),
        by_category={},
        per_query=per_query
    )
