# Changelog

Every change that can move a score, change what is published, or change how a run is made. Newest first. The scorer version is stored in every summary; the leaderboard marks rows scored with an older one, and `python3 -m bambench rescore --track <track>` brings them up to date from saved outputs without running a model.

## Unreleased, towards v0.1 (planned 30 November 2026)

### 25 November 2026

**Dashboard**

- BAM look: Verdana, the BAM petrol, cyan and red, a dark header bar. Verdana ships with Windows and macOS, so the hosted copy still loads no font from outside.
- The overview opens with leaders at a glance: highest overall, cheapest and fastest within 5 points of the top, best model of 4B or fewer, best on tables, best on German pages. A lead inside the runner-up's 95% range says so.
- The leaderboard's speed chart becomes score against cost, time or tokens, with the corner above the median score and below the median cost shaded and a line through the systems nothing beats on both. New: systems ranked by one measure, and score against model size. Colour and marker shape show the kind of system: document VLM, general VLM, or pipeline. Each kind can be hidden from the charts.
- Jump links along the leaderboard, and one tooltip style for every chart, which also shows on keyboard focus.
- No score, metric or export changes.

### 22 November 2026

**Systems**

- DeepSeek-OCR 2 runs with an 8,192-token context, its model limit. vLLM refused to start it at 12,288. Every other card was checked against its model's `max_position_embeddings` and is within it.
- 17 more general vision models, none run yet: Qwen3-VL-2B, Qwen3.5-0.8B, Gemma 4 E2B, InternVL3.5-4B and 2B, Molmo2-4B, Ovis2.5-2B and 9B, Ovis2.6-30B-A3B, Kimi-VL-A3B-Instruct, MiMo-VL-7B-RL-2508, Keye-VL-1.5-8B, Bee-8B-RL, Step3-VL-10B, LLaVA-OneVision-2-8B, Nemotron Nano 12B v2 VL and ERNIE 4.5 VL 28B-A3B. Each architecture is in vLLM 0.32.
- New card key `prompt_suffix`, appended to every prompt. MiMo-VL and Keye-VL use it for the `/no_think` tag that switches their thinking off. No existing card changes, so no score moves.
- The watchlist gains the models looked at and left out this round, with the reason for each.

### 13 November 2026

**Ranking**

- The leaderboard ranks by default on the fair view: each system is scored without the pages whose label started from its own draft. A dagger marks such systems. The all-pages scores are one click away and unchanged.
- Scores by page kind, by language and without own drafts carry their own 95% interval. Published intervals did not move. No scorer version change: no existing score changes.
- Two systems can be compared on the pages both were scored on, with a paired bootstrap on the difference and a count of pages each one wins. Pages either system drafted are left out.

**Second annotator**

- A second person can label a sample of pages without seeing the first label. One label is scored against the other with the benchmark's scorer. The agreement is computed against the first label as it was when the two were compared, so later corrections cannot raise it.

**Records and checks**

- Every run records the versions of the packages it used, the model server version and the commit of the weights. Runs made before this date say "not recorded".
- System cards are checked against `systems/schema/card.schema.json` by `bambench check-cards` and in CI.
- Every system has a status: active, pending, failed, superseded or withdrawn, with a reason. A failed run leaves a note that the local dashboard shows. The hosted copy never carries it.
- `bambench meta` sets a document's year, department, family and split.
- Open-track summaries hold compact per-page scores so the hosted copy can show comparisons. Closed-track summaries never do.

**Dashboard**

- Leaderboard: views by page kind and language, filters, column presets, CSV and PNG export, a chart of the best score against model release date, a panel on how to read the table.
- A page per system with rank per score, the command to run it and its run record. A Data page with the composition of both tracks as counts. Changelog, citation, licence and contact in the dashboard.

### 10 November 2026

**Scorer version 3**

- New score *Numbers*: the share of free-standing numbers printed on a page that the output holds digit for digit, with precision next to it. Pooled over pages. Not part of Overall.
- Scores by page language (`by_lang`) next to scores by page kind.

**Scorer version 2**

- Text is compared independent of notation. Subscripts and superscripts written as HTML tags, as inline LaTeX or as Unicode characters now compare equal. So do hyphen, dash and minus variants, and curly, low and angle quotes. Soft hyphens are dropped. Common LaTeX symbols in inline math (for example `\mu`, `\pm`, `\times`) are read as their characters.
- Less-than and greater-than signs survive. Before, a `<` and a later `>` on the same page could swallow the text between them, and a leading `>` in a table cell was dropped.
- A line break inside a table cell separates words.
- Effect: scores of systems that write `$_2$` or use typographic dashes rise slightly. Scores can also fall where the old rule hid a difference.

**Other**

- 95% bootstrap interval over pages for every score (1,000 resamples, fixed seed).
- `bambench rescore`: scores saved outputs against the current labels.
- `bambench export-site` and a GitLab CI file: read-only copy of the dashboard.
- Local dashboard checks the Host header and refuses cross-site writes.
- Seconds and cost per page are divided by the pages a system read, not by the pages scored.
- Draft labels for the 19 remaining open-track pages. The open track now has 21 labelled pages, up from 2, so open-track scores from before this date are not comparable.

### 3 to 9 November 2026

- Default output limit raised from 4,096 to 8,192 tokens.
- Token counts and cut-off replies recorded per run.
- Time, cost and tokens per page on the leaderboard.
- 19 systems added, 6 start-up failures fixed, repetition-penalty variants of two small models added.
- DeepSeek-style OCR models run with the n-gram repetition guard their publisher specifies.

### 23 October to 3 November 2026

- Page picking, draft-only runs, page kind and language, drafting model recorded per label.
- Each summary also reports the score without the pages a system drafted itself.
- Prompt and scorer brought in line with the annotation rules: figures score by caption only; headers, footers, handwriting and stamps are left out.
- Side-by-side comparison view and Models page.

### 15 October 2026

- First version: text, table (TEDS) and formula metrics, record scoring for certificates, text-layer baseline, local vLLM adapter, dashboard, commit guard for the confidential track.
