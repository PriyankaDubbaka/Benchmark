import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {resolve,join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {cpus,platform,arch} from 'node:os';
import {extractSummary,rankPages} from './baselines';
import {scoreExtraction,scoreRetrieval} from './score';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const args=process.argv.slice(2);const opt=(x:string)=>{const i=args.indexOf(x);return i<0?undefined:args[i+1]};
const pdf=opt('--pdf');
if(!pdf){console.error('Usage: bun src/run.ts --pdf /path/to/Zertifikat_BAM-S005c_rev1.pdf [--out results/local]');process.exit(2)}
const out=resolve(opt('--out')||join(root,'results','local'));await mkdir(out,{recursive:true});
const load=async(p:string)=>JSON.parse(await readFile(join(root,p),'utf8'));
const manifest=await load('data/manifest.json');
const hash=createHash('sha256').update(await readFile(pdf)).digest('hex');
if(hash!==manifest.sha256)throw Error('PDF checksum differs from the frozen pilot; do not score another revision against these labels.');
const start=performance.now();
const text=execFileSync('pdftotext',['-layout',resolve(pdf),'-'],{encoding:'utf8',maxBuffer:10*1024*1024});
const parts=text.split('\f');while(parts.length&&!parts.at(-1)!.trim())parts.pop();
const pages=parts.map((text,i)=>({page:i+1,text}));
if(pages.length!==manifest.page_count)throw Error('Unexpected PDF page count');
const publicQueries=await load('data/queries.json');
const extraction={document_id:manifest.document_id,records:extractSummary(pages)};
const extractionElapsed=performance.now()-start;
const runs=[];
for(const method of ['bm25','tfidf'] as const){const t=performance.now();const rankings=rankPages(pages,publicQueries.queries,method);runs.push({method,rankings,retrieval_ms:performance.now()-t});}
// Gold labels are loaded only after baseline predictions have been generated.
const eg=await load('data/extraction_gold.json'),rg=await load('data/retrieval_gold.json');
const results={benchmark_version:'0.1-draft',status:'SMOKE_TEST_ONLY_NOT_A_HELD_OUT_BENCHMARK',
 annotation_status:eg.annotation_status,document_id:manifest.document_id,pdf_sha256:hash,
 data_summary:{documents:1,pages:pages.length,extraction_records:eg.records.length,queries:rg.queries.length,research_papers:0},
 warning:'Visible single certificate; draft labels; template-specific extraction; page-level retrieval; no generalization or model-ranking claim.',
 environment:{bun:Bun.version,platform:platform(),arch:arch(),cpu:cpus()[0]?.model||'unknown',poppler:execFileSync('sh',['-c','pdftotext -v 2>&1'],{encoding:'utf8'}).trim()},
 timing_notes:'One local run. Extraction time includes PDF text decoding. Retrieval time excludes text decoding. Not hardware-comparable performance estimates.',
 extraction:{baseline:'poppler_layout_summary_regex_visible_template',extraction_ms:extractionElapsed,...scoreExtraction(eg.records,extraction.records,pages.length)},
 retrieval:runs.map(r=>({baseline:r.method,parameters:r.method==='bm25'?{k1:1.2,b:0.75}: {tf:'1+ln(f)',idf:'ln((N+1)/(df+1))+1',normalization:'cosine',query_tf:'binary'},retrieval_ms:r.retrieval_ms,...scoreRetrieval(rg.queries,r.rankings,pages.length)}))};
const save=async(name:string,x:any)=>writeFile(join(out,name),JSON.stringify(x,null,2)+'\n');
await save('extraction_predictions.json',extraction);
for(const r of runs)await save(r.method+'_predictions.json',{document_id:manifest.document_id,rankings:r.rankings});
await save('metrics.json',results);
console.log(JSON.stringify({out,status:results.status,data:results.data_summary,extraction_f1:results.extraction.record_f1,retrieval:results.retrieval.map(r=>({baseline:r.baseline,...r.aggregate}))},null,2));
