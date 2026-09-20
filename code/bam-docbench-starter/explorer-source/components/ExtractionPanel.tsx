import React, {useState} from 'react';
import {data} from '../data';
export const ExtractionPanel:React.FC=()=>{
 const [filter,setFilter]=useState('all');const rows=data.extraction.records.filter((r:any)=>filter==='all'||r.status===filter);
 return <div className="flex flex-col gap-4">
  <div className="card bg-base-200"><div className="card-body"><h2 className="card-title">Summary-record extraction</h2><p className="text-3xl font-semibold">{data.metrics.extraction.exact_records} / {data.metrics.extraction.gold_records}</p><p>Exact records reproduced by a rule-based parser adapted to this visible certificate.</p><p className="text-sm text-base-content/60">A software smoke test, not 100% accuracy on unseen BAM documents. No table-structure, general layout or mathematical-equation scoring is implemented yet.</p></div></div>
  <div className="flex items-center gap-3"><h3 className="font-semibold">Draft reference records</h3><select aria-label="Certification status" className="select select-bordered select-sm" value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All rows</option><option value="certified">Certified</option><option value="information_only">Information only</option></select></div>
  <div className="overflow-x-auto"><table className="table table-zebra table-sm"><thead><tr><th>Element</th><th>Value</th><th>Unit</th><th>Expanded U</th><th>k</th><th>Calculated oxide</th><th>Status</th><th>PDF page</th></tr></thead><tbody>{rows.map((r:any)=><tr key={r.element}><td className="font-semibold">{r.element}</td><td>{r.value}</td><td>{r.unit}</td><td>{r.expanded_uncertainty}</td><td>{r.coverage_factor}</td><td>{r.oxide_formula?`${r.oxide_formula}: ${r.oxide_value} ${r.unit}`:'Not listed'}</td><td><span className={'badge badge-sm '+(r.status==='certified'?'badge-outline':'badge-warning')}>{r.status.replaceAll('_',' ')}</span></td><td>{r.source_page}</td></tr>)}</tbody></table></div>
  <p className="text-sm text-base-content/60">Uncertainty applies to the elemental mass fraction. Bracketed oxide quantities are calculated, not independently certified measurands. P and Se must not be promoted to certified status.</p>
 </div>;
};
