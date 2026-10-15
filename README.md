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
git config core.hooksPath .githooks          # once per clone: blocks commits of closed-track files
python -m bambench list                       # documents and systems
python -m bambench run pdftotext-rules        # baseline on the open track
python -m bambench serve                      # dashboard on http://127.0.0.1:8765
python -m unittest discover -s tests -t .     # tests
```

Add an internal report (copied into `data/closed/`, never committed):

```sh
python -m bambench add /path/report.pdf --track closed --id dept-report-001 --department "3.3" --type report
```

or use **Documents → Add a PDF** in the dashboard.

## Tasks and metrics

| Task | Output | Metric |
| --- | --- | --- |
| E1 Text | Page Markdown | 1 − normalised edit distance, tables and formulas removed |
| E2 Tables | HTML or pipe tables | TEDS per gold table (and TEDS-S for structure only) |
| E3 Formulas | `$$ LaTeX $$` | 1 − normalised edit distance on normalised LaTeX (CDM planned) |
| E5 Records | Certificate measurement rows | Exact-record F1, plus critical errors (unit, status, uncertainty) |
| Overall | | Mean of E1, E2 and E3, as in OmniDocBench |

Gold for a page is Markdown in `data/<track>/annotations/<doc>/page-NNN.json` with a status
of `draft`, `checked` or `skip`. Write it in the dashboard's annotation view, prefilled from
Poppler text or from a model's last run, and correct it against the page image.

## Systems

System cards live in `systems/*.json`. Kinds:

- `pdftotext_rules`: Poppler text, the floor baseline.
- `docling`: Docling layout + TableFormer (`pip install docling`).
- `vllm`: any vision model served by vLLM on localhost (or a host named in
  `BAMBENCH_ALLOWED_HOSTS`). The adapter refuses every other host.

On the shared GPU, see [`slurm/README.md`](slurm/README.md).

## Layout

```
bambench/           package: corpus, gold, metrics, systems, runner, server, cli
data/open/          manifests and annotations for public documents
data/closed/        confidential track (gitignored except its README)
dataset/            the public certificate PDFs
systems/            one JSON card per system
results/<track>/summaries/   one score summary per system (closed: aggregates only)
site/               dashboard frontend, plain HTML/JS, no build step
slurm/              batch job that starts vLLM and runs a system
code/               earlier prototypes (bam-docbench-starter, bam-vlm-bench), kept for reference
```

The protocol behind this benchmark is in `code/bam-docbench-starter/docs/benchmark-proposal.md`.
