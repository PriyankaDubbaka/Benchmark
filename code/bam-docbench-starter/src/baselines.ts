import type {RecordRow,Ranking} from './score';
export type Page={page:number;text:string};
// Visible-document heuristic, NOT a held-out extraction model. No reference labels are read.
export function extractSummary(pages:Page[]):RecordRow[]{
 const rows:RecordRow[]=[]; const num='(\\d+(?:\\.\\d+)?)';
 const withOxide=new RegExp('^\\s*([A-Z][a-z]?)\\s+\\(([A-Za-z0-9]+)\\)\\s+'+num+'\\s+\\('+num+'\\)\\s+'+num+'\\s*$');
 const elemental=new RegExp('^\\s*([A-Z][a-z]?)\\s+'+num+'\\s+'+num+'\\s*$');
 for(const p of pages.filter(p=>p.page<=2)){
  let unit:'%'|'mg/kg'='%';let status:RecordRow['status']='certified';
  const k=p.text.match(/coverage factor of k\s*=\s*(\d+(?:\.\d+)?)/i);if(!k)continue;
  for(const line of p.text.split('\n')){
   if(/Values for Information/i.test(line))status='information_only';
   if(/in mg\/kg/.test(line))unit='mg/kg';
   const m=line.match(withOxide),n=line.match(elemental);
   if(m) rows.push({element:m[1],oxide_formula:m[2],value:m[3],oxide_value:m[4],expanded_uncertainty:m[5],unit,status,coverage_factor:Number(k[1]),source_page:p.page});
   else if(n)rows.push({element:n[1],value:n[2],expanded_uncertainty:n[3],oxide_formula:null,oxide_value:null,unit,status,coverage_factor:Number(k[1]),source_page:p.page});
  }
 }
 return rows;
}
const stop=new Set('a an and are as at be by does for from how in is it of on or that the their this to what which with'.split(' '));
function tokens(s:string){return (s.toLowerCase().match(/[\p{L}\p{N}]+/gu)||[]).filter(t=>!stop.has(t))}
export function rankPages(pages:Page[],queries:{id:string;query:string}[],method:'bm25'|'tfidf'):Ranking[]{
 const counts=pages.map(p=>{const m=new Map<string,number>();for(const t of tokens(p.text))m.set(t,(m.get(t)||0)+1);return m});
 const lengths=counts.map(m=>[...m.values()].reduce((a,b)=>a+b,0));const avgdl=lengths.reduce((a,b)=>a+b,0)/pages.length;
 const df=new Map<string,number>();for(const c of counts)for(const t of c.keys())df.set(t,(df.get(t)||0)+1);
 const n=pages.length,k1=1.2,b=0.75;
 const idf=(t:string)=>Math.log((n+1)/((df.get(t)||0)+1))+1;
 const docNorm=counts.map(c=>Math.sqrt([...c].reduce((s,[t,f])=>s+((1+Math.log(f))*idf(t))**2,0)));
 return queries.map(q=>{
  const qt=[...new Set(tokens(q.query))];const qNorm=Math.sqrt(qt.reduce((s,t)=>s+idf(t)**2,0));
  const ranked=pages.map((p,i)=>({page:p.page,score:qt.reduce((s,t)=>{
   const f=counts[i].get(t)||0;if(!f)return s;
   if(method==='bm25'){const d=df.get(t)||0;return s+Math.log(1+(n-d+0.5)/(d+0.5))*f*(k1+1)/(f+k1*(1-b+b*lengths[i]/avgdl))}
   return s+(1+Math.log(f))*idf(t)**2/((docNorm[i]*qNorm)||1);
  },0)})).sort((a,b)=>b.score-a.score||a.page-b.page);
  return {query_id:q.id,pages:ranked.map(r=>r.page)};
 });
}
