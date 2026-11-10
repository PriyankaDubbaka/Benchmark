# Changelog

Every change that can move a score, change what is published, or change how a run is made. Newest first. The scorer version is stored in every summary; the leaderboard marks rows scored with an older one, and `python3 -m bambench rescore --track <track>` brings them up to date from saved outputs without running a model.

## Unreleased, towards v0.1 (planned 30 November 2026)

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
