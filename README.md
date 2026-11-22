# BAM Extraction Benchmark (PW2)

How well do local, open-weight systems pull text, tables, formulas and measurement records
out of BAM technical documents? This repository holds the corpus manifests, reference
annotations, scorers, system adapters and a local dashboard.

Two tracks share one scorer:

- **Open track:** public BAM reference-material certificates (and later CC BY papers). Anyone can rerun it.
- **Closed track:** internal BAM reports. PDFs, labels and raw outputs stay in `data/closed/`,
  which Git ignores and a pre-commit hook guards. Only aggregate scores leave.

## Quick start

Needs Python 3.10+ and Poppler (`pdftotext`, `pdftoppm`, `pdfinfo`). The core has no Python
dependencies.

```sh
git config core.hooksPath .githooks           # once per clone: blocks commits of closed-track files
python3 -m bambench list                       # documents and systems
python3 -m bambench run pdftotext-rules        # baseline on the open track
python3 -m bambench serve                      # dashboard on http://127.0.0.1:8765
python3 -m unittest discover -s tests -t .     # tests
python3 -m bambench rescore --track open       # rescore saved outputs after labels or the scorer change
python3 -m bambench export-site public         # read-only copy of the dashboard for GitLab Pages
python3 -m bambench check-cards                # check every system card against its schema
python3 -m bambench meta <document> --year 2014 --family <name> --split test   # edit a document's manifest
```

## Annotating internal reports

1. Add the report. It is copied into `data/closed/` and never committed:

   ```sh
   python3 -m bambench add /path/report.pdf --track closed --id dept-report-001 --family dept-report
   ```

   or use **Documents → Add a PDF** in the dashboard.

2. Pick 4 to 6 pages, one of each kind the report has, on the document page in the dashboard
   or with `python3 -m bambench mark dept-report-001 1,4,7,18,28`.

3. Draft them with a local model on the GPU (see [`slurm/README.md`](slurm/README.md)):

   ```sh
   sbatch --gres=gpu:4g.40gb:1 slurm/serve_and_run.sbatch qwen3.5-9b closed --draft-only
   ```

4. In the dashboard, open each picked page, **Prefill** from the run, correct the text against
   the page image, set the page kind and language, and save as draft. Recheck it after a
   couple of days and save it as checked.

Scanned reports have no text layer, so the Poppler prefill comes back empty on them. The page
records which source its first draft came from, and every summary also shows the score without
the pages a system drafted itself.

## Tasks and metrics

| Task | Output | Metric |
| --- | --- | --- |
| E1 Text | Page Markdown | 1 − normalised edit distance, tables and formulas removed |
| E2 Tables | HTML or pipe tables | TEDS per gold table (and TEDS-S for structure only) |
| E3 Formulas | `$$ LaTeX $$` | 1 − normalised edit distance on normalised LaTeX (CDM planned) |
| E5 Records | Certificate measurement rows | Exact-record F1, plus critical errors (unit, status, uncertainty) |
| Numbers | Free-standing numbers on the page | Share reproduced digit for digit, pooled over pages. Not part of Overall |
| Overall | | Mean of E1, E2 and E3, as in OmniDocBench |

Gold for a page is Markdown in `data/<track>/annotations/<doc>/page-NNN.json` with a status
of `marked` (picked, no text yet), `draft`, `checked` or `skip`, plus its kind and language. Write it in the dashboard's annotation view, prefilled from
Poppler text or from a model's last run, and correct it against the page image.

### Time and cost

Next to the scores, the leaderboard shows seconds per page, an estimated euro cost per 1,000
pages and the tokens a model wrote per page. Time is the run's wall time with the model already
loaded. Cost is the share of one A100 80 GB the card's `slice` takes (20 GB is a quarter, 40 GB
a half, no slice is CPU and free) times that time times an hourly price, €2 unless
`BAMBENCH_A100_EUR_PER_HOUR` says otherwise. It is for comparing systems, not a bill. Token
counts and replies cut off at `max_tokens` (8,192 unless a card sets its own) come from the vLLM server's usage field, so they
appear only for `vllm` runs made after this was added; older summaries still get time and cost.

## Systems

System cards live in `systems/*.json`. The Models page in the dashboard lists them all with
their claimed capabilities and scores; `systems/watchlist/models.json` holds models not added
yet and why. Kinds:

- `pdftotext_rules`: Poppler text, the floor baseline.
- `docling`: Docling layout + TableFormer (`pip install docling`).
- `vllm`: any vision model served by vLLM on localhost (or a host named in
  `BAMBENCH_ALLOWED_HOSTS`). The adapter refuses every other host. `output` converts a
  model's own format (`deepseek_grounding`, `dots_layout`, `doctags`) to Markdown.
- `paddleocr_vl`, `glm_ocr`, `mineru_vl`: two-stage parsers (layout, then each block) whose
  VLM runs in the same local vLLM server. PaddleOCR and GLM-OCR run from their own
  environments; see [`slurm/README.md`](slurm/README.md#two-stage-parsers).

On the shared GPU, see [`slurm/README.md`](slurm/README.md).

## Layout

```
bambench/           package: corpus, gold, metrics, systems, runner, server, cli
data/open/          manifests and annotations for public documents
data/closed/        confidential track (gitignored except its README)
dataset/            the public certificate PDFs
systems/            one JSON card per system
results/<track>/summaries/   one score summary per system; closed ones only via `bambench export-closed`
site/               dashboard frontend, plain HTML/JS, no build step
slurm/              batch job that starts vLLM and runs a system
code/               earlier prototypes (bam-docbench-starter, bam-vlm-bench), kept for reference
```

## Documentation

| File | What it holds |
| --- | --- |
| [docs/project-documentation.md](docs/project-documentation.md) | Purpose, method, data, systems, results, history, limitations, decisions |
| [docs/datasheet.md](docs/datasheet.md) | The dataset in the Datasheets for Datasets format |
| [docs/data-management-plan.md](docs/data-management-plan.md) | Data management plan under the BAM Data Policy |
| [docs/compliance-checklist.md](docs/compliance-checklist.md) | BAM, DFG, FAIR and legal rules with status and open actions |
| [docs/gap-analysis-and-roadmap.md](docs/gap-analysis-and-roadmap.md) | Comparison with other benchmarks, weaknesses, next features and models |
| [docs/annotation-guide.md](docs/annotation-guide.md) | Labelling rules |
| [docs/hosting-on-gitlab.md](docs/hosting-on-gitlab.md) | Publishing the read-only dashboard with GitLab Pages |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Every change that can move a score |

The first protocol draft is in `code/bam-docbench-starter/docs/benchmark-proposal.md`.
