// BAM DocBench starter: offline, draft-label evaluators. No model calls.
export const fields = ['value','unit','expanded_uncertainty','coverage_factor','status','oxide_formula','oxide_value','source_page'] as const;
export type RecordRow = {element:string; value:string; unit:'%'|'mg/kg'; expanded_uncertainty:string; coverage_factor:number; status:'certified'|'information_only'; oxide_formula:string|null; oxide_value:string|null; source_page:number};
export type Query = {id:string; query:string; category:string; evidence_pages:number[]; relevance:Record<string,number>};
export type Ranking = {query_id:string; pages:number[]};
const avg=(a:number[])=>a.length?a.reduce((s,v)=>s+v,0)/a.length:0;
function assert(x:unknown,msg:string):asserts x {if(!x)throw Error(msg)}
export function decimal(s:unknown):string {
 assert(typeof s==='string' && /^-?\d+(\.\d+)?$/.test(s),'Numeric values must be finite decimal strings, not floats/exponents');
 const neg=s.startsWith('-'); const [a,b='']=s.replace(/^-/,'').split('.');
 const v=(a.replace(/^0+(?=\d)/,'')||'0')+(b.replace(/0+$/,'')?'.'+b.replace(/0+$/,''):'');
 return (neg&&v!=='0'?'-':'')+v;
}
export function validateRows(rows:RecordRow[], pageCount:number) {
 assert(Array.isArray(rows),'records must be an array'); const seen=new Set<string>();
 for(const r of rows){
  assert(r && typeof r==='object','Bad record');
  assert(Object.keys(r).sort().join(',')===['element',...fields].sort().join(','),'Unexpected or missing extraction fields');
  assert(typeof r.element==='string'&&/^[A-Z][a-z]?$/.test(r.element),'Invalid element key');
  assert(!seen.has(r.element),'Duplicate element: '+r.element); seen.add(r.element);
  decimal(r.value); decimal(r.expanded_uncertainty);
  assert(['%','mg/kg'].includes(r.unit),'Unsupported unit');
  assert(['certified','information_only'].includes(r.status),'Invalid status');
  assert(Number.isInteger(r.source_page)&&r.source_page>=1&&r.source_page<=pageCount,'Invalid source page');
  assert(Number.isFinite(r.coverage_factor)&&r.coverage_factor>0,'Invalid coverage factor');
  assert(r.oxide_formula===null || (typeof r.oxide_formula==='string'&&/^(?:[A-Z][a-z]?\d*)+$/.test(r.oxide_formula)),'Invalid formula');
  assert((r.oxide_formula===null)===(r.oxide_value===null),'Oxide formula/value null mismatch');
  if(r.oxide_value!==null) decimal(r.oxide_value);
 }
}
function equal(k:string,a:unknown,b:unknown){
 if(a===null||b===null)return a===b;
 if(['value','expanded_uncertainty','oxide_value'].includes(k))return decimal(a)===decimal(b);
 return a===b;
}
export function scoreExtraction(gold:RecordRow[],pred:RecordRow[],pageCount=8){
 validateRows(gold,pageCount); validateRows(pred,pageCount);
 assert(gold.length>0,'Empty reference set');
 const p=new Map(pred.map(r=>[r.element,r])); let exact=0;
 const field_correct=Object.fromEntries(fields.map(f=>[f,0])) as Record<string,number>;
 const errors:{element:string;fields:string[]}[]=[];
 for(const g of gold){const r=p.get(g.element); const wrong:string[]=[];
  for(const f of fields){if(r&&equal(f,g[f],r[f]))field_correct[f]++;else wrong.push(f)}
  if(!wrong.length)exact++;else errors.push({element:g.element,fields:wrong});
 }
 const precision=pred.length?exact/pred.length:0,recall=exact/gold.length;
 return {gold_records:gold.length,predicted_records:pred.length,exact_records:exact,
  record_precision:precision,record_recall:recall,record_f1:precision+recall?2*precision*recall/(precision+recall):0,
  field_accuracy_over_all_gold_records:Object.fromEntries(fields.map(f=>[f,field_correct[f]/gold.length])),
  extra_elements:pred.filter(r=>!gold.some(g=>g.element===r.element)).map(r=>r.element),errors};
}
export function scoreRetrieval(queries:Query[],pred:Ranking[],pageCount=8){
 assert(Array.isArray(pred),'rankings must be an array'); assert(queries.length>0,'Empty query reference');
 const ids=new Set(queries.map(q=>q.id)); assert(ids.size===queries.length,'Duplicate reference queries');
 const ranks=new Map<string,number[]>();
 for(const r of pred){assert(r&&typeof r==='object','Bad ranking');assert(ids.has(r.query_id),'Unknown query ID');assert(!ranks.has(r.query_id),'Duplicate query ID');
  assert(Array.isArray(r.pages)&&r.pages.every(p=>Number.isInteger(p)&&p>=1&&p<=pageCount),'Invalid page ranking');
  assert(new Set(r.pages).size===r.pages.length,'Duplicate ranked page'); ranks.set(r.query_id,r.pages);
 }
 const per_query=queries.map(q=>{
  assert(q.evidence_pages.length>0,'Unanswerable queries need a separate protocol');
  const pages=ranks.get(q.id)||[], relevant=Object.keys(q.relevance).filter(p=>q.relevance[p]>0).map(Number);
  assert(relevant.length>0,'No positive relevance labels');
  const o:Record<string,number>={};
  for(const k of [1,3,5]){
   const top=pages.slice(0,k);o['recall_at_'+k]=top.filter(p=>relevant.includes(p)).length/relevant.length;
   const j=top.findIndex(p=>relevant.includes(p));o['mrr_at_'+k]=j<0?0:1/(j+1);
   const dcg=top.reduce((s,p,i)=>s+(2**(q.relevance[String(p)]||0)-1)/Math.log2(i+2),0);
   const ideal=Object.values(q.relevance).sort((a,b)=>b-a).slice(0,k).reduce((s,g,i)=>s+(2**g-1)/Math.log2(i+2),0);
   o['ndcg_at_'+k]=ideal?dcg/ideal:0;
   o['complete_evidence_at_'+k]=q.evidence_pages.every(p=>top.includes(p))?1:0;
  }
  return {id:q.id,category:q.category,ranking:pages,...o};
 });
 const metricKeys=Object.keys(per_query[0]).filter(k=>!['id','category','ranking'].includes(k));
 const means=(rows:any[])=>Object.fromEntries(metricKeys.map(k=>[k,avg(rows.map(r=>r[k]))]));
 return {query_count:queries.length,submitted_queries:ranks.size,aggregate:means(per_query),
  by_category:Object.fromEntries([...new Set(queries.map(q=>q.category))].map(c=>[c,means(per_query.filter(q=>q.category===c))])),per_query};
}
