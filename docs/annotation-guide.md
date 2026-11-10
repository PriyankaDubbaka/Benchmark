# Annotation guide

How reference labels for the benchmark are written. The same rules apply to both tracks. The prompt for general vision models in `bambench/systems/vllm_vlm.py` asks for the same conventions, so a model is never penalised for following the instruction.

## The short version

1. **Annotate pages, not documents.** Pick 4 to 6 pages per report, one of each kind the report has. The benchmark only runs and scores the pages you annotate, so a 60 page report costs the same as a 10 page one.
2. **Never type from scratch.** Let a local model write the first draft, then correct it against the page image. Correcting is several times faster than typing, and it matters most for tables.
3. **Write what is printed, in reading order, in both languages.** Leave out what a reader would skip: running headers and footers, the logo, page numbers, handwriting, signatures, stamps, and the text inside drawings.

## 1. Choosing pages

Your reports don't follow a template, but their pages do fall into a handful of kinds. Set the kind in the Page kind field when you save the page:

| Kind | Typical page | Why it matters |
| --- | --- | --- |
| `cover` | title block, revision table, sign-off table | short mixed layout, small tables |
| `prose` | numbered sections, often English with German under it | E1 text, reading order, umlauts |
| `figure` | drawings with callouts, plots, photos | tests that models don't dump labels into the text |
| `table` | result tables, work report forms with merged headers | E2 TEDS, the hardest and most useful pages |
| `form` | blank or partly filled form | empty grid structure |
| `formula` | calculation pages | E3 |
| `mixed` | a page with several of the above in similar shares | all tasks |

A 28 page report with a cover, prose, drawings, work report forms and a blank form gives five pages, one of each kind. Two table pages instead of one is fine if a report is mostly tables.

Rules of thumb:

- Per week, aim for about 3 reports × 5 pages, which matches the 15 pages a week in the plan.
- Across the corpus, keep the mix roughly 30% table, 25% prose, 15% figure, 15% cover/form, and formula pages whenever you find them. Tables are where the systems differ most, so they earn the extra share.
- Skip pages that are blank, near-duplicates of a page you already did (the same form with other rows), or unreadable. Mark them `skip` only if you opened them; untouched pages simply stay unannotated.
- Give related reports the same `family_id` when you add them (all revisions of one report and the work reports that belong to it). Splits are made by family, so a revision can't leak from dev into test.

## 2. The drafting workflow

A scan has no text layer, so **Prefill from pdftotext gives an empty box on every page**. That is true for most older reports. The draft has to come from a model.

The routine:

1. Add the PDF on the closed track (Documents → Add a PDF, or `python3 -m bambench add`).
2. On the document page, type the page numbers into **Pick pages to annotate** and click Pick. Picked pages turn blue. On the command line: `python3 -m bambench mark <id> 1,4,7,18,28`.
3. Draft every picked page on the GPU in one job: `sbatch --gres=gpu:4g.40gb:1 slurm/serve_and_run.sbatch qwen3.5-9b closed --draft-only`. Nothing is scored.
4. On each page, pick the run next to Prefill and click Prefill. Correct the text against the image, set the page kind and language, and save as `draft`. The tool records which model wrote the first draft.
5. After at least two days, reopen the page, check it against the image again, and save as `checked`. Only checked pages count on the test split.

Which model drafts: a general vision model that follows the full instructions, so its drafts come with HTML tables and without headers or handwriting. Every model you draft with gets an advantage on those pages, because the gold starts from its output. The tool records the drafting model per page, and each summary also shows the score without the pages a system drafted itself. Switch between two drafting models per report family, so that no single system holds the advantage on all pages.

## 3. What goes into the Markdown

**Text**
- Reading order is column by column, top to bottom. On the bilingual pages that means the English sentence, then the German sentence under it, exactly as printed.
- Keep German characters as they are: ä ö ü ß, never ae or ss. Keep ® and other symbols.
- Use `#`, `##` for real headings. Don't bother with bold or italics; the scorer ignores formatting.
- Lists keep their numbers or bullets. Hyphenated line breaks are joined ("Konservie-rung" becomes "Konservierung").

**Tables**
- Write every table as HTML with `colspan` and `rowspan`. Form headers need merged cells, and pipe tables can't express them. Pipe tables are fine only for simple grids.
- One cell per printed cell. Both languages in one cell stay in one cell, separated by a space.
- Empty cells stay as empty `<td></td>`. They carry structure.
- Leave handwritten entries out of the cell (dates, initials, ticks). Printed labels such as "Date/ Datum:" stay.

**Figures and drawings**
- Write only the caption as a line of text, in both languages if both are printed.
- Don't transcribe callouts or labels inside the drawing. Their position is the information, and Markdown can't hold it. OmniDocBench treats figure regions the same way.

**Formulas**
- Display formulas as LaTeX between `$$` and `$$`, inline ones between `$` and `$`.
- Use plain LaTeX: `\frac`, `\sqrt`, `_{}`, `^{}`, `\cdot`, `\,` for units. Units in roman: `\mathrm{N/mm^2}`.
- Numbered equations: drop the number "(3)" unless it's part of the text.

**Leave out**
- Running header (logo, company line), footer (document code, "Page 5 of 17"), page numbers.
- Handwriting, signatures, stamps, and scanner marks.

**Notes to yourself**
- Anything between `<!--` and `-->` is ignored by the scorer. Use it for doubts: `<!-- unsure: 913-915 or 913-916 -->`.

## 4. Pace

Rough times with a model draft: prose 5 min, cover 5 min, figure 2 min, table 15 to 25 min, formula page 10 min. A five page report with one table is about 45 minutes plus a 15 minute re-check two days later. Do the re-check on fresh eyes first thing in a session, before new drafting.

**Choices made on the open track, to keep or change consistently**

These came up while drafting the public certificates. Whatever is decided, apply it to every page.

- A block with two people side by side (name, role) is read person by person, left then right.
- A contact block with two columns (phone and fax, e-mail and internet) is read column by column.
- A framed note with a logo beside it is written as text. The logo and the text inside it are left out.
- Footnotes printed inside a table frame are written as text below the table.
- Column-group labels printed above a table grid are written as a first table row with `colspan`.
- A list aligned in columns without any lines is a table when it has a header row, and text when it has none.
- A standalone equation on its own line is a display formula, including short ones.
- A word printed with a gap or an obvious slip is written as printed, with a comment if it could be read two ways.
- Numbers keep their printed form. A decimal comma stays a comma.
