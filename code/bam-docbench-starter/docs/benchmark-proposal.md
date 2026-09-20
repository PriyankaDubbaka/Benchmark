# BAM DocBench
## Technical-document extraction and evidence retrieval
**Working proposal v0.1 • 18 September 2026 • Prepared for Priyanka, Mehran and Philipp**

**Status:** a runnable, single-certificate pilot plus a proposed release protocol. Not an official BAM benchmark, an expert-validated dataset, or a public launch. The name is provisional. Research papers are source candidates, not yet part of the scored corpus.

## 1. The benchmark we should build

**Research question:** Which document-processing systems accurately recover technical information and retrieve its supporting evidence from reference-material certificates and research papers?

The first release should serve PW2 (extraction evaluation) and PW4 (retrieval evaluation). It should compare complete, specified systems—not vaguely labelled “LLMs”—because parsers, OCR, chunking, embeddings and rerankers can each determine the outcome. A non-LLM system is a valid competitor.

Philipp’s Matbench Discovery reference is an example of scientific benchmark infrastructure: explicit tasks, fixed data, task-appropriate metrics, reproducible submissions and a usable public comparison site. We should adopt those practices, not its materials-discovery metrics or a cosmetic copy of its leaderboard. Separate extraction and retrieval rankings are preferable to an arbitrary combined score.

### Scope boundaries

- **Included:** technical PDF extraction, measurement semantics, evidence retrieval, reproducibility and source/version traceability.
- **Interfaces, not replacement projects:** PW1/PW3 supply systems to evaluate. AP8 informs provenance fields. Mohamed retains knowledge-graph construction and KG evaluation; Alp retains expert-workflow and cognitive/agent evaluation.
- **Not first-release claims:** regulatory approval, safe autonomous inspection, KG correctness, reasoning superiority over experts, or reliable interpretation of engineering drawings.
- **External validity:** certificates and papers are a useful public proxy, not a representative sample of confidential package-design safety reports. Success here does not establish performance on those reports. A separate BAM-local transfer study would be needed later.

## 2. What has actually been built

The starter contains an offline runner, draft annotations, two page-retrieval baselines, a template-specific extraction baseline, prediction validators, scoring functions, automated tests and a results explorer.

The frozen input is the uploaded eight-page `Zertifikat_BAM-S005c_rev1.pdf`. Its own content identifies **BAM-S005c V2**, accepted 19 August 2020 and revised **3 March 2025**. The filename is not the version authority. SHA-256 in `data/manifest.json` binds results to the exact uploaded bytes; the runner refuses a different file.

- **Extraction:** 27 elemental mass-fraction records: 25 certified rows on PDF page 1 and two information-only rows on page 2. Fields include value, unit, expanded uncertainty, coverage factor, certification status, calculated oxide formula/value and source page.
- **Retrieval:** 16 answerable English queries over all eight pages, including multi-page evidence tasks. Reference answers are annotation aids, not a scored answer-generation task.
- **Labels:** machine-assisted drafts checked against the supplied document, including visual checks of the summary tables. They have not been independently validated by BAM experts.
- **Baselines:** Poppler layout-text plus summary-row rules; BM25; and TF-IDF cosine retrieval. All are CPU-only and can run without network access once Bun and Poppler are installed. They were executed in this working environment, not on BAM infrastructure.
- **Tests:** 18 automated scorer/interface tests passed. These test software behavior, not scientific validity of the labels.

### Important traps in the example

1. Al is 0.587% with expanded uncertainty 0.018%; its bracketed Al2O3 value is calculated. The uncertainty must not silently be assigned to the oxide value.
2. Percent and mg/kg appear in different sections of the same table. A number without its unit is not a correct measurement extraction.
3. P and Se are **information-only**, not certified values. Their uncertainty from interlaboratory certification was too large for certification.
4. The coverage factor is k = 2, approximately 95% confidence. This is expanded uncertainty, not an ordinary standard deviation or a scoring tolerance.
5. Accepted individual laboratory results and mean-of-means tables are not interchangeable with the certified summary. Missing/outlier markers must not become numerical zeroes.
6. The uploaded V2 certificate is valid until producer revocation. An alternate official-hosted certificate encountered during source research gives a different validity statement. These must remain separate versions, not be merged.

**Pilot limitation:** a page is a very coarse retrieval unit, and retrieving five of only eight pages is an easy test. The extraction rules were written with this document visible. Neither high extraction accuracy nor the pilot’s baseline ordering demonstrates generalization. See `pilot-results.md` for the actual measurements and limitations.

## 3. Corpus design

Use two independently reported collections:

**A — Reference-material certificates.** Start with BAM certificates spanning different material families and certificate templates: glasses, metals/alloys, environmental matrices and other suitable categories, subject to availability and permissions. Include certified and non-certified values, varied units, uncertainty notation, conditions, revisions and footnotes.

**B — Openly licensed research papers.** Prefer measurement-focused materials science, analytical chemistry and metrology. Include tables, equations, multi-column layouts, captions, experimental conditions and uncertainty reporting. Record paper type; a review is not the same stratum as experimental research. Avoid selecting only unusually clean PDFs.

Proposed v1 planning envelope: **100 documents, about 300 selected extraction pages and 300 retrieval queries**, roughly balanced between the two collections. These are targets, not current counts or a statistical power claim. The full documents remain in the retrieval corpus; only identified pages/regions are extraction evaluation targets. Publish denominators for each element and query category. Resize after measuring annotation effort.

A lower-risk development milestone is **20 documents, about 60 extraction pages and 60 queries**. Cover multiple independent certificate families and paper templates before expanding volume. The uploaded certificate belongs only to development, because its content and labels have already been inspected.

### Candidate papers already identified

The accompanying source register documents article-specific CC BY statements for:

- Fang et al., *Development of a Water Matrix Certified Reference Material for Volatile Organic Compounds Analysis in Water* — DOI 10.3390/molecules26144370.
- Mourda et al., *Reference Materials for Thermal Conductivity Measurements: European Situation* — DOI 10.3390/buildings14092795.
- Rychlik et al., *Ensuring Food Integrity by Metrology and FAIR Data Principles* — DOI 10.3389/fchem.2018.00049.

These are candidates for inspection and sampling, not an adequate representative research-paper corpus by themselves. PDF versions and checksums still need freezing; third-party figure/table exceptions must be checked before inclusion.

### Rights and release gate

Public access is not an open-license grant. Public availability of the BAM certificate is established; redistribution/derivative permissions are not. Obtain BAM’s written permission or an applicable explicit license before publishing PDFs, crops, extracted text or their derivative dataset. Until then, retain a source manifest and use locally supplied files for the pilot. Do not relabel third-party documents under the software’s eventual license.

For papers, store the exact article license, attribution, source URL, access date, version and any figure/table exceptions. Prefer CC BY/CC0 for a broadly reusable release. A freely readable article or an arXiv upload without a suitable reuse grant is not automatically eligible. No documents or results have been published by this work.

## 4. Track E — Extraction (PW2)

**Input:** original PDF or prescribed page image. **Output:** a canonical structured document containing page regions, element types, reading order, table grids/cells, formulas and selected measurement records. Supply text/OCR and multimodal divisions separately if their input access differs.

### E1: Structural extraction

Proposed v1 metrics:

- Text: character error rate under a frozen normalization rule; report language and scan-quality strata.
- Layout: element precision/recall/F1 after one-to-one matching of same-class boxes at IoU ≥ 0.5; report class-wise denominators. Reading order is pairwise precedence accuracy over matched elements, alongside detection recall so missing elements are visible.
- Tables: TEDS-Structure for topology and normalized cell-content accuracy/F1 for aligned cells. Report both; correct grid geometry does not imply correct numerical content.
- Formulas: normalized exact match plus token edit distance. Specify LaTeX normalization and allowed equivalents; do not promise algebraic equivalence based on string matching or an LLM judge. Distinguish display equations from chemical formulas.

These metrics need implementation and expert-reviewed structural annotations. The current pilot does **not** implement bounding-box evaluation, TEDS, reading-order scoring or general mathematical-formula scoring.

### E2: Technical measurement records

A valid record links **measurand + value + unit + uncertainty definition + qualification + evidence**. Certificate records include certification status and optional calculated oxide quantities. Papers additionally need applicable conditions, sample identity and whether uncertainty/error is SD, SE, expanded uncertainty or unspecified. Missing information must remain explicitly unspecified, not guessed.

For the current certificate pilot, records match on the case-sensitive elemental symbol. Exact-record precision = completely correct records / predicted records; recall = completely correct records / reference records; F1 is their harmonic mean. All eight non-key fields must match. Extra predictions reduce precision, missing predictions reduce recall, duplicates are invalid. Field accuracies use all reference records as denominator, so missing rows do not disappear from reporting.

The pilot accepts equivalent decimal spellings such as `33.10` and `33.1`, but does not allow numerical deviation. Units and chemical formulas are case-sensitive canonical strings; unit conversion is not implemented. Measurement uncertainty is **never** used to excuse extraction error. A later physical-value normalization metric may permit approved unit conversions, but must remain separate from faithful source transcription.

For v1, report certificate and paper scores separately; use document-macro averages with element-level diagnostics. Publish critical-error counts for wrong units, wrong uncertainty type and false certification status alongside record recall. No aggregate score should conceal these errors.

## 5. Track R — Evidence retrieval (PW4)

**Question:** Can a system find all relevant evidence, not merely generate a plausible answer?

Create expert-written queries for numerical/table lookups, qualification/footnotes, methods, source/version identification and multi-region or multi-document evidence. Questions should reflect plausible user needs and avoid gratuitous page-number hints. Version-ambiguous requests must be disambiguated in the task or explicitly annotated as such.

### Separate retrieval from parsing

- **R-reference:** every system receives identical human-corrected text, tables and canonical evidence-region IDs. This isolates retrieval.
- **R-PDF, later:** systems ingest the same raw PDFs and build their own representations. Results capture extraction plus retrieval and must not share the R-reference ranking.

The current pilot is neither a full R-reference release nor a multi-document search benchmark: it is a single-PDF page-search smoke test using a common Poppler extraction for both baselines.

### Evidence and scoring protocol

For v1, freeze evidence units before comparing systems: text paragraphs, table rows with inherited headers/units and linked footnotes, equations with definitions, and appropriate caption/figure regions. Give every unit a stable document-version ID and page/box or text-span locator. Map system chunks to these units without giving a giant chunk credit for every item it overlaps. Use canonical-unit rankings as the main controlled track; report token-budget evidence coverage separately for freely chunked systems.

Relevance: 2 = directly supports a requested fact; 1 = useful supporting context; 0 = irrelevant. Recall and reciprocal rank use positive relevance; nDCG uses gain 2^grade − 1. Use **nDCG@10** as the proposed main v1 retrieval sorting metric, with Recall@5/10/20 and MRR@10. Multi-part tasks also report **complete-evidence success**: whether a permitted complete set of required evidence is present. Annotate alternative sufficient evidence sets when several locations independently support the same fact; do not demand retrieval of redundant copies.

The pilot implements Recall, MRR, nDCG and complete-evidence success at k = 1, 3 and 5. Its evidence pages are conjunctive required pages; alternative evidence sets are not implemented. Missing query submissions score zero. Duplicate pages, unknown queries and invalid page IDs are rejected.

V1 should include a separately scored set of unanswerable/insufficient-evidence queries. A top-k retriever alone cannot be expected to abstain: require a confidence/abstention output for that subtrack, calibrate its threshold on development data and report answerable coverage plus false-support rate on unanswerable cases. Do not insert zero-positive queries into ordinary recall/nDCG averages.

The pilot reference answers are not assessed for generated-answer correctness. LLM-as-judge scoring and complex reasoning evaluation are not required for this first release.

## 6. Gold standard, splits and leakage

1. Freeze source files, rights, family groups and target pages before annotation. Preserve raw strings as well as normalized values and evidence locations.
2. Use model-assisted annotation only as a draft. Qualified humans validate it. Double-annotate every validation/test target independently, adjudicate disagreements, and audit a random development subset. Include all critical measurement/status fields in the audit.
3. For retrieval, pool candidates from distinct retrievers and manual search; independently assess relevance. Record judgment coverage. Newly discovered relevant evidence triggers an annotation correction and rescoring of all affected systems, not preferential treatment of one submission.
4. Report pre-adjudication agreement: field exact agreement for extraction and weighted agreement plus category-level disagreement for relevance. Set release thresholds after the initial annotation study; unresolved critical numerical/status disagreements block release.
5. Create approximately 60/20/20 development/validation/test partitions by **document family**, stratified by document type and difficulty where feasible—not random pages. Keep certificate predecessors/revisions/translations, associated reports, paper preprint/publisher versions and supplements together. Deduplicate exact files, text and templates.
6. Record cross-family links: a paper reproducing a certificate table or reporting its certification can leak answers. Merge connected families into one split or exclude the overlapping material.
7. Distinguish an in-template holdout from a more difficult held-out-family/template evaluation. With too few independent families, publish only a development dataset, not a confident generalization claim.
8. Public source documents may already have been in model pretraining. Request training-data and cutoff disclosures, including “unknown.” Hidden labels reduce benchmark-specific tuning but cannot establish absence of pretraining contamination.

Use family-cluster bootstrap intervals for v1 comparisons and paired resampling for system differences; specify the seed and resample count. Do not present confidence intervals from this one-family pilot as population estimates. Final sample size should follow observed variance, coverage and the smallest decision-relevant performance difference.

## 7. Reproducibility and the public comparison site

Each submission should identify system/model/checkpoint versions, licenses, training overlap disclosure, parser/OCR, chunking, embeddings, reranker, prompt/configuration, seeds, hardware, software environment, code commit, corpus/annotation/scorer hashes and prediction artifacts. Freeze environment files or container digests. Log runtime and peak memory under a declared protocol; mark unmeasured fields as unmeasured. Separate local/open-weight systems from cloud/API systems, if a public-data API division is approved.

For the BAM project, preserve its explicit local-operability constraint. Public inputs do not themselves authorize use of commercial cloud models on BAM infrastructure. The starter requires no external model service; a later API comparison would be a separate decision.

The site should show task tabs, dataset/version badges, corpus and difficulty filters, sortable task metrics, uncertainty intervals, failure-category breakdowns, model/data openness and hardware/resource disclosure. Each row links to a reproducible system card and artifacts. Never fabricate model rows or use demo numbers without unmistakable labelling.

Recommended first launch: documented submissions through reviewed repository changes, automated schema checks and canonical scoring. Use a fresh hidden-label challenge set for the official ranking if maintenance capacity exists; otherwise explicitly label public-test results and tuning exposure. Rate-limit challenge submissions to reduce overfitting. Governance for hidden labels and result review must be assigned before opening submissions.

The supplied explorer is a **local pilot-results viewer**, not a hosted public submission service. It displays only actual runs on the single visible certificate.

## 8. Delivery plan to year-end

This plan interprets Philipp’s “this year” as 2026. It is a proposal, not an agreed resource commitment or an inferred project-start date.

- **By 2 October:** agree scope and owners, resolve certificate rights, confirm local compute, sample certificate families and paper types, time the annotation process.
- **By 23 October:** assemble the 20-document development corpus, validate schemas and annotation guide, review the first expert-labelled tasks; add one modern document parser and one dense retriever to the existing simple baselines.
- **By 13 November:** freeze family splits, expand towards the agreed v1 volume, complete independent validation/test annotation and adjudication. If expert capacity is insufficient, reduce corpus size rather than reference quality.
- **By 4 December:** run at least three materially different systems per supported track under the same protocol; verify reproducibility, failure analyses and confidence intervals where justified.
- **By 18 December:** present the versioned dataset, protocol, real comparison results, reproducible runner and website. Publish only assets whose rights are cleared. Remaining unsupported tracks are visibly deferred.

**Illustrative staffing:** 0.8–1.0 FTE engineering/benchmark ownership; pooled 0.4–0.6 FTE domain annotation and adjudication; a named lead for scope, rights and release decisions. This is a planning envelope, not a request already approved by Mehran or Philipp. The initial annotation timing study must determine whether it supports the proposed scale.

**Suggested responsibility split, for agreement:** Priyanka owns technical delivery; Mehran/Philipp sponsor scope and resources; certificate/metrology experts validate reference data; Mohamed/Alp provide interface and domain-task input without transferring their core PhD packages. A rights owner and a second independent annotation reviewer must be named.

### Definition of a presentable benchmark

A frozen, documented corpus; rights-cleared release assets; expert-validated labels; leak-resistant splits; tested and versioned metrics; multiple reproducible baselines; honest limitations; and a results website backed by real artifacts. A polished leaderboard without these is not a finished benchmark.

## 9. Decisions still needed from the team

1. Who can independently validate certificate quantities, uncertainty definitions and relevance labels?
2. Who can authorize BAM certificate redistribution, and under what terms?
3. What engineering/annotation capacity and local hardware are available through December?
4. Which application-focused paper topics and document languages matter most? The pilot uses English because the supplied certificate is English; German/multilingual coverage should be selected deliberately.

## Sources

- User-provided *Package Design Assessment · Project and PhD Work Packages*: PW2/PW4 (p4), AP8 (p7), on-premise constraint (p9).
- User-provided *Extended Synopsis: AI-Enhanced Documentation Analysis in Regulatory Safety Assessment of Transport Packages*: technical motivation and architecture; its broader local/cloud discussion does not override the more specific work-package constraint.
- User-uploaded BAM-S005c V2 certificate, especially pp1–2 and p8. Exact bytes identified by the manifest hash.
- Matbench Discovery: https://matbench-discovery.materialsproject.org/benchmarks ; https://matbench-discovery.materialsproject.org/contribute .
- Official BAM and publisher-specific sources, license evidence and version caveats: `corpus-source-register.md`.
