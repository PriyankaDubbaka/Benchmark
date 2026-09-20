# Pilot results — actual run, not a general benchmark

**Version:** 0.1-draft. **Input:** one visible BAM-S005c V2 certificate; 8 pages, 27 draft extraction records and 16 draft answerable retrieval queries. **Scored research papers: 0.**

## Extraction

The Poppler-layout summary-row rule baseline reproduced **27/27 complete records**, giving exact-record precision, recall and F1 of 100.00%. The parser was designed against this visible certificate format. This is a successful software smoke test, **not** an estimate of accuracy on unseen documents or a claim of perfect technical-document understanding. General layout, table topology and mathematical-equation extraction are not scored.

## Retrieval

Both baselines received identical Poppler page text and question strings, without reference answers or relevance labels during ranking. Scores below use all 16 questions. Recall is the fraction of all positively judged pages recovered, not just whether one page was found. Complete evidence requires every required page for the query.

| Baseline | Recall@1 | Recall@3 | nDCG@3 | MRR@3 | Complete evidence@3 |
| --- | --- | --- | --- | --- | --- |
| BM25 | 70.83% | 88.54% | 83.93% | 86.46% | 81.25% |
| TFIDF | 73.96% | 91.67% | 87.67% | 90.63% | 81.25% |

- **BM25** did not retrieve a complete required evidence set in the top three pages for 3 of 16 queries: Q05, Q11, Q14. Inspect their per-query rankings and draft judgments before drawing conclusions.
- **TFIDF** did not retrieve a complete required evidence set in the top three pages for 3 of 16 queries: Q05, Q10, Q14. Inspect their per-query rankings and draft judgments before drawing conclusions.

These numbers do not establish a scientifically meaningful winner. Some questions have multiple required pages; many require one. All pages come from the same certificate, all queries are visible, and relevance is a machine-assisted draft rather than independently adjudicated expert gold. At k=5, retrieval already covers most of the eight-page corpus, so high recall is unsurprising. No parameter changes were made after observing these results.

## Provenance and runtime

The PDF is bound to SHA-256 `a556ad0b36a5eb75ba706ceb37c51412be4ca2f3b5a0d39085b32f37bb2204b9`. The document itself says V2, revised 2025-03-03; filename suffixes are not authoritative. The runner rejects a different PDF hash. Raw PDF/source text is not redistributed in the starter.

Recorded environment: Bun 1.3.14, linux/x64; CPU: AMD EPYC. The Poppler version string, one-run elapsed times and complete predictions are in `results/pilot/metrics.json` and the adjacent prediction files. Extraction elapsed time includes PDF text decoding; retrieval elapsed time excludes it. These timings are not normalized hardware-comparison results. Peak memory, GPU usage and energy were not measured.

The run used no network model service. It took place in this working environment, not on BAM machines. The code can be run offline on approved local infrastructure once dependencies are installed. Eighteen scorer/interface tests passed, including exact/empty outputs, incorrect units/status, numerical errors inside uncertainty bounds, missing fields, extra records, duplicates, invalid page IDs and incomplete multi-page evidence.

## Next scientific step

Have qualified BAM reviewers independently validate the measurement fields and relevance judgments, then add rights-cleared certificates from new material families and eligible paper PDFs. Freeze document-family splits before tuning any stronger systems. The current example must remain in development because it is already visible and has influenced the extraction rules.
