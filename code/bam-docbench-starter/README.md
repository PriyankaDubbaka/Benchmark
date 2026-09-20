# BAM DocBench — working starter v0.1

**A real, runnable smoke test; not a finished scientific benchmark.** Prepared for Priyanka / Team Mehran and Philipp, 18 September 2026. Name and release terms are proposals, not official BAM approval.

## What is included

- One eight-page BAM-S005c V2 certificate task, bound to the exact user-uploaded PDF by SHA-256.
- Draft reference annotations: 27 elemental summary records and 16 answerable page-retrieval queries.
- A visible-template extraction rule baseline, BM25 and TF-IDF page-retrieval baselines.
- Strict prediction validation, exact-record/field extraction scoring and retrieval metrics at 1/3/5.
- 18 passing software tests; recorded predictions, metrics and runtime/environment metadata.
- Full benchmark proposal, source/rights register, pilot-results note and annotation caveats.
- A separate interactive results explorer delivered with this thread.

**Not included:** source PDF (reuse permission unresolved), research-paper PDFs/annotations, expert-validated labels, held-out test data, general table-layout/formula evaluation, modern model runs, containers, public hosting or a submission server. Corpus text is not bundled. None of this work has been publicly published.

## Run offline

Requirements: Bun (tested version is in `results/pilot/metrics.json`) and Poppler's `pdftotext`. On Debian/Ubuntu, Poppler is provided by `poppler-utils`. Install prerequisites using your approved software process; runtime needs no network or model credentials.

Keep the folder structure intact, then run from this directory:

```sh
bun test
bun src/run.ts --pdf /absolute/path/to/Zertifikat_BAM-S005c_rev1.pdf --out results/local
```

Supply the same PDF Priyanka uploaded. `data/manifest.json` fixes its hash; the similarly named source URL is not a promise that future downloaded bytes will match. Do not bypass the hash check or replace gold labels merely to accept another revision.

The runner extracts PDF text, generates predictions without reading gold labels, then evaluates. It records the predictions and metrics in the selected output directory. Existing files in that selected directory are overwritten; use a new directory to preserve a run.

## Evaluate your own predictions

```sh
bun src/evaluate.ts extraction my_extraction.json
bun src/evaluate.ts retrieval my_rankings.json
```

Use the actual `document_id` in `data/manifest.json`. See saved files under `results/pilot/` for complete prediction examples.

Extraction payload: `{ "document_id": "bam-s005c-v2", "records": [...] }`. Each record must contain exactly `element`, `value`, `unit`, `expanded_uncertainty`, `coverage_factor`, `status`, `oxide_formula`, `oxide_value`, `source_page`. Values/uncertainties are decimal **strings**; units are `%` or `mg/kg`; status is `certified` or `information_only`; oxide fields are both null when absent. Emit only elemental rows from summary tables on pages 1–2, not the laboratory data tables.

Retrieval payload: `{ "document_id": "bam-s005c-v2", "rankings": [...] }`. Each ranking contains `query_id` and an ordered `pages` array of unique, 1-indexed PDF page numbers. Query text without answers/relevance is in `data/queries.json`. Missing queries score zero; unknown IDs and duplicate pages are invalid.

## Scoring contract

Extraction matches rows by case-sensitive element key. A true positive requires all other fields correct. Decimal trailing zeros are normalized; numerically different values are not tolerated even when inside the measurement uncertainty. Unit conversion and algebraic equivalence are not implemented. Missing rows reduce recall; extra rows reduce precision. Field accuracy includes missing rows as errors. Invalid schema is rejected, not silently repaired.

Retrieval: relevance > 0 counts as relevant; nDCG uses `2^grade - 1`; MRR finds the first positive item within k. Recall is recovered positive reference pages / all positive reference pages. Complete-evidence success requires all designated evidence pages. Query means are unweighted; category breakdowns are also saved. No unanswerable-query, answer-generation or alternate-evidence-set scoring is implemented in v0.1.

Software oracle tests reuse reference labels as predictions solely to verify expected score 1; they are not listed as model results. The baseline scorer never uses an LLM judge.

## Files

- `docs/benchmark-proposal.md` — full proposed scientific protocol, boundaries, roadmap and release gates.
- `docs/corpus-source-register.md` — official certificate sources and three CC BY paper candidates, including version/rights caveats.
- `docs/pilot-results.md` — real pilot metrics and their limits.
- `data/manifest.json` — identity, revision, source candidate, rights status and checksum.
- `data/extraction_gold.json`, `data/retrieval_gold.json` — draft annotations, NOT independent expert gold.
- `data/queries.json` — retriever-visible questions only.
- `data/annotation-notes.md` — annotation provenance/caveats.
- `src/baselines.ts`, `src/score.ts`, `src/run.ts`, `src/evaluate.ts` — source.
- `tests/score.test.ts` — software checks.
- `results/pilot/` — actual predictions and measurements from the initial run.
- `RELEASE-CHECKLIST.md` — proposed launch gates.

## Reproducibility and interpretation

The extraction heuristic is expressly adapted to the visible summary-table format. BM25 uses k1=1.2, b=0.75. TF-IDF uses log term frequency, smoothed IDF and cosine normalization with binary query terms. Both operate on identical page-level Poppler text, lowercase Unicode alphanumeric tokens, no stemming and the same small stopword list in source. Equal scores break by ascending page number. No parameters were selected using held-out data; there is no held-out data here.

A one-document score is a diagnostic, not evidence of domain performance. Most queries need only one page; retrieving five of eight pages can achieve high recall without sophisticated understanding. Report corpus/version and draft-label status beside every number.

## Rights and contribution status

BAM certificate redistribution is permission-pending. Research-paper candidates have article-specific CC BY statements, but their exact PDF versions, attributions and third-party content exclusions still need registration. This starter does not claim rights over BAM documents, authorise BAM branding, or assign an open-source license on the team's behalf. Agree code and annotation release licenses before public release.
