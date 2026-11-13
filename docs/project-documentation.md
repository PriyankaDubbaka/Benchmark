# BAM Extraction Benchmark (PW2): project documentation

| | |
| --- | --- |
| Project | PW2, benchmark for extracting text, tables, formulas and measurement records from BAM technical documents |
| Author and data steward | Priyanka Dubbaka, BAM |
| Reviewer | [team lead, to fill in] |
| Period covered | 15 October 2026 to 10 November 2026 |
| Software version | 0.1.0, scorer version 3 |
| Status | Working draft for the v0.1 release planned for 30 November 2026 |

This is a living document. It records what was built, why, on which data, and what is still open, so that someone outside the project can check the results and repeat them. Section 11 maps the project to the rules it has to follow. Companion files:

- [datasheet.md](datasheet.md): the dataset, described in the Datasheets for Datasets format
- [data-management-plan.md](data-management-plan.md): the plan the BAM Data Policy asks for
- [compliance-checklist.md](compliance-checklist.md): each rule, its status and the open actions
- [gap-analysis-and-roadmap.md](gap-analysis-and-roadmap.md): comparison with other benchmarks, weaknesses, next features and models
- [annotation-guide.md](annotation-guide.md): the labelling rules
- [hosting-on-gitlab.md](hosting-on-gitlab.md): how to publish the read-only dashboard inside BAM
- [CHANGELOG.md](CHANGELOG.md): every change that can move a score

## 1. Purpose

BAM holds decades of inspection reports, test reports and certificates as PDF. Many are scans. Their content, above all the tables of measured values, is only usable by software after it has been extracted. A growing number of open-weight vision models claim to do this, and their published scores come from benchmarks built on academic papers, textbooks and slides. None of those says how the models behave on a scanned, bilingual BAM report from the early 2000s.

The benchmark answers one question: **which locally runnable, open-weight system extracts BAM documents most faithfully, and at what cost in GPU time?**

The request from the head of division was a benchmark that is ready and presentable within 2026, in the style of [Matbench Discovery](https://matbench-discovery.materialsproject.org/): a public-facing leaderboard backed by a documented method.

Three conditions shaped every decision:

1. **Internal reports never leave BAM.** They may not be sent to any external service, including AI services.
2. **Only open-weight models that run on the shared BAM GPU server**, which in practice means about 27 billion parameters or fewer.
3. **One annotator.** No second person was available for labelling.

## 2. What the benchmark measures

Each system receives one page image at a time and returns Markdown. That output is compared with a reference transcription written by a person.

| Task | What is compared | Metric |
| --- | --- | --- |
| E1 Text | Running text of the page, tables and formulas removed | 1 minus normalised edit distance |
| E2 Tables | Each reference table against its best-matching predicted table | TEDS (structure and cell content) and TEDS-S (structure only) |
| E3 Formulas | Display formulas in LaTeX | 1 minus normalised edit distance on normalised LaTeX |
| Numbers | Free-standing numbers printed on the page | Share reproduced digit for digit (recall), and precision |
| E5 Records | Measurement rows of a certificate: element, value, unit, uncertainty, status | Exact-record F1 plus counts of critical errors (wrong unit, wrong status, wrong uncertainty) |
| Overall | | Mean of E1, E2 and E3, the same construction as OmniDocBench |

Next to accuracy the leaderboard reports seconds per page, an estimated cost per 1,000 pages, tokens written per page and the number of replies cut off at the token limit.

Every score carries a 95% interval from a bootstrap over pages (1,000 resamples, fixed seed). Scores are also broken down by page kind (cover, prose, table, figure, form, formula, mixed) and by language (en, de, en+de).

**Why a separate Numbers score.** A measured value with one wrong digit is a wrong value. Edit distance barely registers it: 0.587 read as 0.578 costs two characters on a page of two thousand. For a metrology institute this is the error that matters most, so it is counted on its own. It stays out of Overall so that Overall remains comparable with other benchmarks.

**What is not measured yet** is listed in section 9.

## 3. Data

Two tracks share one scorer.

| | Open track | Closed track |
| --- | --- | --- |
| Content | Public BAM reference-material certificates | Internal BAM reports |
| Documents | 5 | 54 registered |
| Pages | 21, all with a draft label | 17 with a label on 9 November; target 60 or more |
| Where it lives | In this repository | `data/closed/` on the BAM GPU server only |
| Who can rerun it | Anyone with the repository | BAM staff with access to the server |
| What may be published | Everything, once redistribution rights are confirmed | Aggregate scores, and only when 20 or more pages back them |

The closed track is the one that counts. Its documents cannot have been seen by any model during training, which no public benchmark can promise. The open track exists so that the method can be checked and rerun by people without access to the reports.

Reports are long, so pages are sampled: four to six pages per report, one of each kind the report has. The benchmark runs and scores only labelled pages. Full detail is in the [datasheet](datasheet.md) and the [annotation guide](annotation-guide.md).

## 4. Method

### 4.1 Reference labels

1. The annotator picks the pages of a report.
2. A model writes a first draft. On the closed track this is an open-weight model running on the BAM GPU server. The page records which model it was.
3. The annotator corrects the draft against the page image and saves it as `draft`.
4. After at least two days the annotator checks the page again and saves it as `checked`.

Only `checked` pages count on the test split. A system is ranked without the pages whose labels started from its own draft, because it has a head start on those. The leaderboard marks such a system and shows both scores.

A second annotator can label a sample of pages without seeing the first label. Scoring one label against the other gives the agreement between two people, which is the ceiling a system can be measured against. The procedure is in section 5 of the [annotation guide](annotation-guide.md#5-the-second-annotator).

### 4.2 Running a system

A system is described by one JSON card in `systems/`: model, licence, the exact serve command, prompt, image resolution and output converter. A Slurm job starts a vLLM server on one GPU slice, bound to localhost, runs the system over the labelled pages and stops the server. The adapter refuses any host that is not local. Outputs are stored per page, so scores can be recomputed later without running the model again (`bambench rescore`).

General vision models receive one fixed instruction (in `bambench/systems/vllm_vlm.py`). Dedicated OCR models receive the prompt their publisher specifies, because they are trained on it and fail on anything else. Decoding is greedy. The output limit is 8,192 tokens unless a card sets its own.

### 4.3 Scoring

- Text is normalised before comparison so that the same printed text compares equal in any notation: Unicode NFKC, subscripts and superscripts in HTML, inline LaTeX or Unicode, dash and quote variants, soft hyphens, Markdown marks.
- Pipe tables and HTML tables are converted to the same tree before TEDS.
- Running headers, footers, handwriting, signatures, stamps and text inside drawings are left out of the reference, and the prompt tells models to leave them out.
- The scorer is pure Python with no model in the loop. There is no LLM judge.
- Every summary records the scorer version. The leaderboard marks rows scored with an older version.

### 4.4 Safeguards for the confidential track

- `data/closed/` is ignored by Git, and a commit hook refuses any file from it, including names with umlauts.
- Model endpoints must be on localhost or on a host explicitly allowed by an environment variable.
- Two-stage parsers that could call a vendor API are started with their cloud mode off and with the proxy variables pointed at a dead port.
- The dashboard binds to localhost, checks the Host header and rejects cross-site writes.
- Closed-track scores leave the server only through `bambench export-closed`, which requires 20 or more scored pages per system.
- The hosted read-only copy contains no closed document names, page text, images or raw outputs.

## 5. Software

```
bambench/           corpus, gold labels, metrics, system adapters, runner, server, CLI
data/open/          manifests and labels for the public documents
data/closed/        confidential track, ignored by Git
dataset/            the public certificate PDFs
systems/            one JSON card per system
results/            score summaries
site/               dashboard, plain HTML and JavaScript, no build step
slurm/              batch job that serves a model and runs a system
tests/              unit tests
docs/               this documentation
```

The core needs Python 3.10 or later and Poppler, and has no Python dependencies. vLLM is needed only on the GPU server.

Commands: `list`, `add`, `meta`, `mark`, `run`, `rescore`, `leaderboard`, `check-cards`, `export-closed`, `export-site`, `serve`, `guard`.

The dashboard has an overview, a leaderboard with views, filters, export and two charts, a page per system, a comparison of two systems, a Models page with the status of every system, a Data page with the composition of both tracks, a document browser, an annotation view with prefill, a blind view for a second annotator, a side-by-side view of the page image, the reference and each system's output, and the changelog.

## 6. Systems

39 system cards on 10 November 2026: one text-layer baseline, one classical layout pipeline, and 37 cards for open-weight vision models from 0.26 to 31 billion parameters (two of the 37 are decoding variants of a model that is already listed). Publishers include Alibaba, Google, Mistral AI, LightOn, IBM, Z.ai, Baidu, Ai2, Shanghai AI Lab, Microsoft, OpenBMB, DeepSeek, rednote and Hugging Face.

The weights are published under Apache-2.0 or MIT. Four cards note extra conditions: a separate licence agreement for dots.mocr, toolkit terms for MinerU, a research and education note on olmOCR 2, and research-only training data for one model. Three older cards still say that the licence must be verified on the model card. The Poppler baseline is GPL-2.0.

Models whose licence excludes the EU, or which need an outside API, are not in the benchmark. `systems/watchlist/models.json` keeps the list and the reason for each. A model's licence was read from its model card when the system card was written; BAM's legal office has not reviewed them.

## 7. Results on 10 November 2026

**Open track.** 21 pages, all with draft labels. Only the text-layer baseline has been run on all 21: Overall 22.2 (95% interval 17.3 to 35.1), text 66.7, tables 0.0, numbers 100.0. This is the expected floor: the text layer of a born-digital PDF holds every number, and Poppler alone produces no table structure. The vision models have not been run on the open track since the 19 new pages were added.

**Closed track.** 32 systems have been run on 17 labelled pages. These results are interim and internal. They rest on fewer than 20 pages and on draft labels, so by the project's own rule they are not printed here. They are visible in the dashboard on the BAM GPU server. Three observations hold regardless of the exact numbers:

1. The model that drafted the labels scores far above all others on those pages. This is the head-start effect, and it is why every summary also reports the score without a system's own drafts.
2. Small models loop on long table pages under greedy decoding and run into the token limit. Raising the limit does not help; the count of cut-off replies is now shown next to each score.
3. Dedicated OCR models of 1 to 4 billion parameters cost a fraction of the large general models per page at similar interim accuracy.

Final numbers will be produced after the label freeze, on `checked` pages only, and published with `export-closed`.

## 8. History

| Date | What happened |
| --- | --- |
| 15 Oct | Project started. Research, design and implementation plan written. Decision to keep the existing repository and restructure it into one package. Conditions fixed: models up to 27B, one annotator, release on 30 November, a working dashboard from the first day. |
| 15 Oct | Phase 1 built and merged: package, text, table and formula metrics, five public certificates registered, text-layer baseline, local vLLM adapter, dashboard. A review before the merge found ten defects. The two most serious could have let confidential report files be committed. All ten were fixed. |
| 20 Oct | Annotation approach for long scanned reports settled: sample pages, draft with a local model, correct by hand. Annotation guide written. |
| 23 Oct | Software installed on the BAM GPU server. 54 internal reports registered in the closed track. First drafting run with a local 9B model. |
| 23 Oct | Annotation tool extended: page picking, draft-only runs, page kind and language, drafting model recorded per page. Side-by-side comparison view and Models page added. |
| 23 Oct to 3 Nov | 14 systems running. Per-kind scores. Progress presented on 3 November. Licence review of candidate models against EU usability. |
| 3 to 9 Nov | Time, cost and token columns added. 19 more models added. Six that failed to start were fixed. Output limit raised from 4,096 to 8,192 tokens. Repetition-penalty variants added to test the looping problem. 32 systems scored on 17 closed pages. |
| 10 Nov | Bootstrap intervals, rescoring without reruns, read-only hosted copy with GitLab CI, request guard for the local dashboard. Scorer versions 2 and 3: notation-independent text comparison, number fidelity, per-language scores. Draft labels for the 19 remaining open-track pages. This documentation. |

Planned: label freeze on 20 November, final runs on frozen labels, release v0.1 on 30 November. An earlier proposal in `code/bam-docbench-starter/docs/benchmark-proposal.md` names different dates (family splits frozen by 13 November, presentation by 18 December). Which set applies needs to be confirmed with the team lead.

## 9. Limitations

These are stated plainly because guideline 12 of the DFG Code asks for it and because a reader deciding which model to use needs them.

1. **One annotator.** There is no agreement figure between annotators. The re-check after two days catches slips, not systematic habits.
2. **All labels are still drafts.** No page has the status `checked` yet.
3. **Small sample.** With 17 pages the intervals are wide and most neighbouring systems cannot be told apart.
4. **Labels start from model drafts.** The drafting model is favoured on its own pages. On the open track the drafts came from the page image and the Poppler text layer, which favours text-layer baselines on numbers.
5. **No test split yet.** All documents are marked `dev`. Prompts and output converters were tuned while looking at these pages.
6. **Formula metric is string-based.** Two LaTeX strings that render the same can still differ. There are few formula pages.
7. **Reading order, figures and charts are not scored separately.**
8. **Records (E5) exist for one certificate only.**
9. **One run per system, one prompt, one image resolution.** Sensitivity to these is not measured. Requests are sent one at a time, so the time column understates what a model achieves with batching.
10. **Cost is an estimate** from the GPU slice share and a flat hourly price. It is for comparing systems, not a bill.
11. **Model revisions are not pinned.** Cards name the model repository, not the commit of the weights.
12. **Rights on the public certificates are unconfirmed.** They are publicly accessible; permission to redistribute them has not been obtained.
13. **Some public certificates are also registered in the closed track** and must be removed from it before the freeze.

How each of these will be closed is in [gap-analysis-and-roadmap.md](gap-analysis-and-roadmap.md).

## 10. Decisions and their reasons

| Decision | Reason |
| --- | --- |
| Two tracks | The valuable data is confidential. A public track lets others verify the method. |
| Page sampling instead of whole documents | One annotator cannot label 54 long reports. Sampling one page of each kind keeps coverage. |
| Model-drafted, human-corrected labels | Correcting is several times faster than typing, above all for tables. The bias it introduces is measured and reported. |
| Markdown with HTML tables as the reference format | Merged cells in BAM forms cannot be written as pipe tables. The same format is used by OmniDocBench, so results are comparable in construction. |
| No LLM judge | A judge model would be one more unverified system, and a confidential page could not be sent to an external one. |
| Scores recomputable from saved outputs | Labels change during re-checks, and GPU time on a shared server is scarce. |
| 20-page threshold for publishing closed scores | A score from a handful of pages can reveal which pages they were and is statistically weak. |
| Numbers kept out of Overall | Keeps Overall comparable with other benchmarks while still reporting what BAM cares about most. |
| Prompt of the publisher for OCR models, one fixed prompt for general models | OCR models fail on instructions they were not trained on. Each system is tested as its publisher intends it to be used. |

## 11. Rules this project follows

The full mapping with status and evidence is in [compliance-checklist.md](compliance-checklist.md). In short:

- **BAM Code to ensure scientific integrity (2023)** and **BAM Data Policy**: documentation from raw data to result, a data management plan, structured metadata, storage in the BAM Data Store, retention for ten years, source code archived centrally.
- **DFG Guidelines for Safeguarding Good Research Practice (2019, version 1.1 of 2022)**: guidelines 7, 10, 11, 12, 13, 14 and 17.
- **DFG statement on generative models (September 2023)**: disclose whether, which, for what and how far AI tools were used. See section 12.
- **FAIR principles** for the data and **FAIR4RS** for the software.
- **GDPR and BDSG** for names and signatures in the reports.
- **Regulation (EU) 2024/1689 (AI Act)** and the licences of the models.
- **Datasheets for Datasets** and the **BetterBench** checklist as the documentation standard for the benchmark itself.

Open points that need a decision from BAM, not from the author alone: the software licence, the move of the repository from a personal GitHub account to BAM GitLab, deposit in the BAM Data Store, redistribution rights for the public certificates, and a look by the data protection officer.

## 12. Use of AI tools

> Author: read this section, correct it where needed and confirm it before you submit. It is here because the DFG statement of September 2023 asks researchers to disclose the use of generative models, and the BAM Code binds staff to the DFG guidelines.

- **Subject of the study.** The systems under evaluation are AI models. All of them ran on BAM hardware.
- **Label drafting, closed track.** First drafts were written by open-weight models on the BAM GPU server and corrected by the author. The drafting model is recorded per page. No internal document, page image, label or model output was sent to an external service.
- **Label drafting, open track.** First drafts of the 21 public certificate pages were written with an AI assistant from the page images and the Poppler text layer. Every number was checked by program against the text layer. The author's check of these pages is pending.
- **Software and documentation.** Source code, tests and this documentation were written with an AI coding assistant (Claude Code, Anthropic) under the author's direction. The author ran the software on BAM hardware and reviewed its results.
- **Responsibility.** The author is responsible for the content of the benchmark, its labels and its results. An AI tool is not an author.

## 13. How to reproduce

```sh
git clone <repository>
cd Benchmark
git config core.hooksPath .githooks
python3 -m unittest discover -q tests          # all tests pass
python3 -m bambench run pdftotext-rules        # baseline on the open track
python3 -m bambench serve                      # dashboard on http://127.0.0.1:8765
```

A vision model on the open track, on a machine with a GPU and vLLM:

```sh
sbatch --gres=gpu:2g.20gb:1 slurm/serve_and_run.sbatch lightonocr-2-1b open
```

After labels change, without running any model:

```sh
python3 -m bambench rescore --track open
```

Each run folder holds the outputs per page. Its summary records the system card as used, the software and scorer version, the Python version, the platform and the GPU.

## 14. References

- Deutsche Forschungsgemeinschaft. *Guidelines for Safeguarding Good Research Practice. Code of Conduct.* September 2019, revised version 1.1, April 2022.
- Deutsche Forschungsgemeinschaft, Executive Committee. *Statement on the influence of generative models for text and image creation on science and the humanities and on the DFG's funding activities.* September 2023. The document carries a note that it was revised in December 2025; check the current version.
- Bundesanstalt für Materialforschung und -prüfung. *Code to ensure scientific integrity of BAM.* 23 January 2023.
- Bundesanstalt für Materialforschung und -prüfung. *BAM Data Policy: Leitlinien zum Umgang mit Forschungsdaten an der BAM.*
- Wilkinson, M. D. et al. *The FAIR Guiding Principles for scientific data management and stewardship.* Scientific Data 3, 160018 (2016).
- Barker, M. et al. *Introducing the FAIR Principles for research software.* Scientific Data 9, 622 (2022).
- Gebru, T. et al. *Datasheets for Datasets.* Communications of the ACM 64(12), 2021.
- Reuel, A. et al. *BetterBench: Assessing AI Benchmarks, Uncovering Issues, and Establishing Best Practices.* arXiv:2411.12990, 2024.
- Ouyang, L. et al. *OmniDocBench.* CVPR 2025. https://github.com/opendatalab/OmniDocBench
- Zhong, X., ShafieiBavani, E., Jimeno Yepes, A. *Image-based table recognition: data, model, and evaluation* (TEDS). ECCV 2020.
- Riebesell, J. et al. *A framework to evaluate machine learning crystal stability predictions* (Matbench Discovery). Nature Machine Intelligence 7, 836 to 847 (2025).
- olmOCR-Bench, Allen Institute for AI. https://github.com/allenai/olmocr
- ParseBench, LlamaIndex, April 2026. arXiv:2604.08538.
