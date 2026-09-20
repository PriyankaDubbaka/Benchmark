import {readFile} from 'node:fs/promises';
import {dirname,resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {scoreExtraction,scoreRetrieval} from './score';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const [task,file]=process.argv.slice(2);
if(!['extraction','retrieval'].includes(task)||!file){console.error('Usage: bun src/evaluate.ts extraction|retrieval predictions.json');process.exit(2)}
const load=async(p:string)=>JSON.parse(await readFile(p,'utf8'));
const m=await load(join(root,'data/manifest.json')),pred=await load(resolve(file));
if(pred.document_id!==m.document_id)throw Error('Document ID mismatch');
const g=await load(join(root,'data',task+'_gold.json'));
const metrics=task==='extraction'?scoreExtraction(g.records,pred.records,m.page_count):scoreRetrieval(g.queries,pred.rankings,m.page_count);
console.log(JSON.stringify({benchmark_version:'0.1-draft',status:'SMOKE_TEST_ONLY_NOT_A_HELD_OUT_BENCHMARK',annotation_status:g.annotation_status,task,metrics},null,2));
