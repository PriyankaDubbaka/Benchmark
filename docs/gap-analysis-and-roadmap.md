# Gap analysis and roadmap

What other benchmarks do that this one does not, where a critical reviewer would push, what was closed on 10 November 2026, and what to build and run next. Facts about other benchmarks were read from their own pages on 10 November 2026.

## 1. How it compares

| | This benchmark | OmniDocBench v1.7 | olmOCR-Bench | ParseBench | Matbench Discovery |
| --- | --- | --- | --- | --- | --- |
| Field | BAM technical documents | General PDF parsing | General PDF parsing | Enterprise documents | Materials stability prediction |
| Size | 21 public pages, 17 internal so far | 1,651 pages | single-page PDFs with pass or fail facts | about 2,000 pages, over 167,000 rules | not comparable |
| Languages | English, German, bilingual pages | English, Chinese | not stated | not stated | n/a |
| Unseen by models | Closed track: yes, by construction | No, public | No, public | No, public | n/a |
| Text | Edit distance | Edit distance, BLEU, METEOR | Presence and absence facts | Rule pass rate | n/a |
| Tables | TEDS, TEDS-S | TEDS, edit distance | Cell and neighbour facts | Record match by column header | n/a |
| Formulas | Edit distance on LaTeX | CDM (rendered comparison) | Rendered, symbol by symbol | Not separate | n/a |
| Reading order | Inside the text score only | Scored on its own | Pairwise order facts | Rule type | n/a |
| Charts | Not scored | Not scored | Not scored | Spot values with tolerance | n/a |
| Number fidelity | Yes, own score | No | No | Partly, in table records | n/a |
| Measurement records with unit and uncertainty | Yes, one document so far | No | No | No | n/a |
| Uncertainty of scores | 95% bootstrap interval on every score | None stated | Plus-minus values, method not stated | None stated | n/a |
| Cost and speed | Seconds, euro per 1,000 pages, tokens, cut-offs | No | No | No | Parameters, training cost optional |
| Label process | Model draft, one annotator, second look after two days | Manual plus model annotation, expert check | Model-assisted, manual review, some second passes | Model labels, every page reviewed | n/a |
| Annotator agreement | None | Not stated | Not stated | Not stated | n/a |
| Label bias control | Score without a system's own drafts | None stated | None stated | None stated | Field `test_set_informed` |
| Page attributes | Kind, language | Language, layout, rotation, background, table type, scan quality, watermark | Seven document categories | Five dimensions | n/a |
| Submission | Add a system card | Local evaluation | Local run | Local run | Pull request with a validated YAML file |
| Model metadata | JSON card: licence, serve command, prompt, slice | Result tables | Result table | Result table | YAML with schema, lifecycle, licences, environment |
| Paper, DOI, citation file | Citation file only | CVPR 2025 | arXiv | arXiv | Journal paper, Figshare, citation file |

Three things stand out.

**Where this benchmark is ahead.** Documents no model has seen. German and bilingual pages. A score for numbers. Intervals on every score. Cost next to accuracy. A measured correction for label bias. None of the three document benchmarks reports intervals, and BetterBench found that 14 of 24 well-known AI benchmarks report neither statistical significance nor uncertainty.

**Where it is behind.** Size by two orders of magnitude. No rendered formula metric. No separate reading-order score. No chart score. No page attributes for scan quality. No paper, no DOI, no licence.

**What was copied from Matbench Discovery,** since that was the model named for this project: one metadata file per model checked against a schema, a status field (pending, active, failed, superseded, withdrawn), a marker for systems that had contact with the labels, automatic checks of a new card in CI, filters and views on the leaderboard, a page per model, a changelog and a citation in the dashboard. Still to copy: predictions archived with a DOI. Matbench Discovery shows no intervals; this benchmark does.

## 2. Weaknesses a reviewer would find

Ordered by how much they threaten the conclusions.

### Label quality

| # | Weakness | Why it matters | Closing it |
| --- | --- | --- | --- |
| 1 | One annotator, no agreement figure | Nobody can say how much of a score difference is label noise | A colleague has agreed to label a sample blind. **The blind view and the agreement score were built on 13 November.** Open until at least 10 pages have a second label |
| 2 | Labels start from a model's draft | The drafting model led the interim closed leaderboard by a wide margin on its own pages | **Closed on 13 November: the leaderboard ranks without a system's own drafts and marks such systems.** Still worth doing: alternate two drafting models by report family |
| 3 | No page is `checked` yet | The test split only counts checked pages | Second look on all pages before 20 November |
| 4 | Label errors go unnoticed | One wrong reference cell lowers every system | Build the disagreement finder: pages where the best systems agree with each other and differ from the label |

### Statistics

| # | Weakness | Why it matters | Closing it |
| --- | --- | --- | --- |
| 5 | 17 pages | If page scores spread with a standard deviation near 0.25, the interval is about ±0.12 at 17 pages, ±0.06 at 60 and ±0.05 at 100. Most neighbours on the leaderboard overlap today. The real intervals appear after `rescore` | More pages. 60 is the minimum for the release, 100 to 150 for firm ranks |
| 6 | Intervals treat pages as independent | Pages of one report share layout, so the true uncertainty is larger | Resample report families instead of pages once there are enough families |
| 7 | No paired comparison | Two overlapping intervals can still hide a consistent winner | **Closed on 13 November: paired bootstrap on the difference of two systems, on the pages both were scored on** |
| 8 | One run per system | Run-to-run variation is unknown | Three runs of the top five systems |

### What is measured

| # | Weakness | Why it matters | Closing it |
| --- | --- | --- | --- |
| 9 | Wrong digits were hidden in edit distance | The worst error for BAM | **Closed on 10 November: Numbers score** |
| 10 | Notation was scored as content | `<sub>2</sub>` against `$_2$` cost points | **Closed on 10 November: scorer version 2** |
| 11 | Formula score is string-based | Equivalent LaTeX can differ | Add CDM or a rendered comparison. Needs a TeX installation on the server |
| 12 | Reading order has no score of its own | Bilingual pages and two-column forms are where order goes wrong | Order score over text blocks |
| 13 | Records exist for one certificate | Values with unit and uncertainty are what BAM would use downstream | Record labels for each certificate family, then for report tables |
| 14 | Plots are skipped | Many reports carry results only as a curve | Later: spot values with tolerance, as ParseBench does |
| 15 | Omission and invention are mixed | A model that drops a paragraph and one that invents one score alike | Report inserted and deleted share of text separately |

### Fairness between systems

| # | Weakness | Why it matters | Closing it |
| --- | --- | --- | --- |
| 16 | No test split | Prompts and converters were tuned on the pages that are scored | Split by report family before the freeze. Tune on dev only |
| 17 | One prompt, one resolution | A model may lose to a setting, not to a rival | Three prompt wordings and two resolutions for the top systems; report the spread |
| 18 | Looping under greedy decoding | Some small models fail on long tables for a decoding reason | Repetition-penalty variants are in; report both settings |
| 19 | Requests sent one by one | Time per page understates batched throughput | Second timing with eight parallel requests |
| 20 | Model revisions not pinned | A publisher can change the weights under the same name | **Recorded for every run from 13 November: weights commit, package versions, model server version.** Older runs need a rerun to carry them |

### Data and governance

| # | Weakness | Why it matters | Closing it |
| --- | --- | --- | --- |
| 21 | Public certificates may be in model training data | Open-track scores can flatter | Treat the closed track as the result, the open track as the demonstration |
| 22 | Public certificates also sit in the closed track | They are not unseen | Remove them before the freeze |
| 23 | Composition of the closed track is undocumented | Readers cannot judge what the scores cover | **The Data page shows counts by kind, language, type, status and draft source since 13 November.** Still open: the datasheet fields, and the year of each report (`bambench meta <document> --year`) |
| 24 | No licence, no DOI, personal GitHub account | Nobody may reuse it, and BAM's rules point to BAM systems | See the [compliance checklist](compliance-checklist.md#6-the-seven-decisions-only-bam-can-take) |
| 25 | Labels exist in one place | A disk fault would cost weeks | Backup before the freeze |

## 3. What is new here

Stated carefully, because each point needs the final data to stand.

1. **A leakage-free benchmark for technical documents of a metrology institute**, with German and bilingual scans. Public benchmarks cannot offer unseen documents.
2. **Number fidelity as a first-class score.** General benchmarks optimise for text similarity. For measured values the right question is whether every digit survived.
3. **Label-drafting bias, measured.** Almost every recent benchmark drafts labels with a model. This one records which model drafted each page and reports the gap.
4. **Accuracy against cost on shared hardware.** Which model is good enough on a quarter of a GPU is the question a public institute actually faces.

## 4. Dashboard features

Built by 10 November: leaderboard with intervals, accuracy against speed chart, time, cost and token columns, Models page, side-by-side page view, annotation view with prefill, scores by kind and by language, Numbers score, markers for stale rows and old scoring, read-only hosted copy.

Built on 13 November, after a feature-by-feature comparison with Matbench Discovery: fair ranking with a marker for systems that drafted labels, views by page kind and language, filters, column presets, a panel on how to read the table, CSV and PNG export, a chart of progress over time, a page per system with rank, run command and run record, status with a reason for every system, system cards checked against a schema in CI, comparison of two systems with a paired interval, the Data page, changelog, citation and contact in the dashboard, and the blind second-annotator view with its agreement score.

Next, in order of value before the release:

| # | Feature | What it gives BAM staff | Effort |
| --- | --- | --- | --- |
| 1 | Disagreement finder | Finds label errors: pages where the best systems agree with each other and differ from the label | small |
| 2 | Annotation progress with recheck queue | Pages checked against the freeze date; drafts older than two days waiting for their second look | small |
| 3 | Pick a model for my documents | Choose page kind, language and GPU budget, get the three best systems | medium |
| 4 | Error breakdown per page | Missing text, invented text, table structure, wrong numbers | medium |
| 5 | Page strip per system | One coloured cell per page, click to open the side-by-side view. Local dashboard only | medium |
| 6 | Page attributes | Scan quality, rotation, handwriting present; scores for each | medium |
| 7 | Release pages with a DOI | Frozen versions that can be cited | small |
| 8 | How to add your documents | A page for other departments: tracks, families, what stays confidential | small |
| 9 | Throughput under load, peak GPU memory and repeat runs | Fairer cost picture and run-to-run spread | medium |
| 10 | Prompt and resolution sensitivity | Shows how stable a rank is | medium |
| 11 | Adjustable weights for Overall | A department can weigh tables higher. The fixed default stays the published one | medium |

## 5. Models

### In the benchmark without a closed-track result on 9 November

| System | What is missing |
| --- | --- |
| Gemma 4 31B (4-bit) | Never submitted. Needs `pip install bitsandbytes`, the download, a 40 GB slice |
| MinerU2.5-Pro | Card exists, not run |
| Granite-Docling | Card exists, not run |
| Docling | Card exists, not run |
| Qwen3.6-27B-FP8 | Card exists; no row on the 9 November leaderboard |
| Qwen3.5-4B and 2B with repetition penalty | Submitted, results not yet read |
| Unlimited-OCR, DeepSeek-OCR 2 | Reruns with the repetition guard did not change their rows; the start-up error lines are needed |

Finishing these comes before adding anything new.

### Worth adding

All were on the licence review of 3 November. Check each model card again before the first run.

| Model | Publisher | Size | Licence as last seen | Why |
| --- | --- | --- | --- | --- |
| GLM-4.1V-9B | Z.ai | 9B | MIT | Earlier model from a publisher already in the benchmark |
| Kimi-VL-A3B | Moonshot | see card | MIT | Small general model |
| MiMo-VL-7B | Xiaomi | 7B | MIT | Mid-size general model |
| Tesseract 5 with a layout step | open source | CPU | Apache-2.0 | The classical floor for scans, where the text-layer baseline returns nothing |

### Only after BAM's legal office has looked

| Model | Condition |
| --- | --- |
| Chandra OCR 2, Surya OCR 2 | Modified OpenRAIL-M; free for research and small organisations, bars competing use. Strong on handwriting and forms |
| MiniCPM-V 4.5 | Own licence, commercial use needs registration |
| olmOCR 2 | Already in; the card speaks of research and education use |

### Watch

| Model | Why not yet |
| --- | --- |
| TeleOCR, OvisOCR2 | Top public scores. Several uploads exist and the original publisher was unclear in October. Both appear in the OmniDocBench repository's own result updates of September 2026, which may settle which upload is the official one |
| PaddleOCR-VL 1.6 | Licence is fine. Left out because it downloads files from its publisher at run time |

### Not usable at BAM

Models whose licence grants no rights in the EU (Meta's multimodal Llama models, Tencent's Hunyuan models), models without open weights, and models too large for one slice of the shared GPU.

## 6. Order of work to 30 November

| When | Labels | Runs | Build |
| --- | --- | --- | --- |
| to 13 Nov | 20 or more closed pages; remove public certificates from the closed track; assign report families | `rescore` on the closed track; finish the pending systems | Disagreement finder, progress view |
| to 20 Nov | 60 closed pages; second look on all; second annotator on 10 pages; **freeze** | All systems on the open track | Family split, pinned revisions, bias-free default |
| to 27 Nov | none | Final runs on frozen labels; three repeats of the top five | Paired comparison, export, composition view |
| to 30 Nov | none | `export-closed`, hosted copy | Release tag, changelog, deposit in the BAM Data Store |
