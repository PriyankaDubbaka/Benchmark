import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import {RetrievalPanel} from './components/RetrievalPanel';
import {ExtractionPanel} from './components/ExtractionPanel';
import {data} from './data';
const App:React.FC=()=>{
 const [tab,setTab]=useState('retrieval');
 return <main className="p-5 flex flex-col gap-5 max-w-6xl mx-auto text-base-content">
  <div role="alert" className="alert alert-warning"><div><strong>Development pilot · draft labels · not an official BAM release</strong><p className="text-sm">Actual offline runs, not invented leaderboard entries. One visible certificate cannot establish model quality or regulatory suitability.</p></div></div>
  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">{[['Documents',data.metrics.data_summary.documents],['Extraction records',data.metrics.data_summary.extraction_records],['Search questions',data.metrics.data_summary.queries],['Scored research papers',data.metrics.data_summary.research_papers]].map(([label,value])=><div key={String(label)} className="card bg-base-200"><div className="card-body p-4"><span className="text-xs text-base-content/60">{label}</span><strong className="text-2xl">{value}</strong></div></div>)}</div>
  <div className="flex flex-wrap gap-2"><span className="badge badge-outline">BAM-S005c V2</span><span className="badge badge-outline">Revised {data.manifest.revision_date}</span><span className="badge badge-outline">8 PDF pages · English</span><span className="badge badge-warning">Redistribution permission pending</span></div>
  <div className="tabs tabs-box" role="tablist"><button role="tab" aria-selected={tab==='retrieval'} className={'tab '+(tab==='retrieval'?'tab-active':'')} onClick={()=>setTab('retrieval')}>Evidence retrieval</button><button role="tab" aria-selected={tab==='extraction'} className={'tab '+(tab==='extraction'?'tab-active':'')} onClick={()=>setTab('extraction')}>Technical extraction</button></div>
  {tab==='retrieval'?<RetrievalPanel/>:<ExtractionPanel/>}
  <details className="collapse collapse-arrow bg-base-200"><summary className="collapse-title font-medium">Reproducibility and next release</summary><div className="collapse-content flex flex-col gap-3 text-sm"><p>Source SHA-256: <code className="break-all">{data.manifest.sha256}</code></p><p>Bun {data.metrics.environment.bun}; {data.metrics.environment.platform}/{data.metrics.environment.arch}. CPU-only. Measured in the working environment, not on BAM infrastructure. The PDF is not embedded or republished here.</p><p>Next: clear certificate rights; freeze eligible research papers; appoint independent domain reviewers; build family-separated datasets; add modern extraction and dense/hybrid retrieval systems.</p><p>Proposal: separate PW2/PW4 leaderboards, not a combined “best AI” score. Knowledge-graph evaluation and expert reasoning remain outside this initial scope.</p></div></details>
 </main>;
};
createRoot(document.getElementById('root')!).render(<App/>);
