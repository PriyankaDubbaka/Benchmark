# Datasheet: BAM Extraction Benchmark corpus

Follows the question groups of *Datasheets for Datasets* (Gebru et al., 2021). Status on 10 November 2026. Fields marked **[fill in]** need facts only the data steward has.

## Motivation

**Why was the dataset created?** To measure how faithfully locally run, open-weight systems extract text, tables, formulas and measurement values from BAM technical documents, and at what cost. Public document benchmarks are built on papers, books and slides and do not contain bilingual, scanned inspection and test reports.

**Who created it and on whose behalf?** Priyanka Dubbaka at the Bundesanstalt für Materialforschung und -prüfung (BAM), as work package PW2. **[fill in: division and team]**

**Who funded it?** **[fill in: BAM budget or project number]**

## Composition

**What does an instance represent?** One page of a PDF document, with a reference transcription in Markdown. A certificate can also carry a list of measurement records.

**How many instances are there?**

| | Open track | Closed track |
| --- | --- | --- |
| Documents | 5 | 54 registered |
| Pages in those documents | 21 | **[fill in]** |
| Pages with a reference label | 21 (all `draft`) | 17 on 9 Nov (all `draft`); target 60 or more |
| Documents with measurement records | 1 | 0 |

Open-track label pages by kind: 9 table, 8 prose, 3 mixed, 1 formula. They hold 13 reference tables, 3 display formulas and 1,355 free-standing numbers.

Closed-track label pages by kind and language: **[fill in from the leaderboard's by-kind and by-language tables]**

**Is it a sample of a larger set?** Yes, twice over. The 54 reports are a selection from BAM's archive: **[fill in: how they were chosen, which departments, which years]**. Within each report, four to six pages are picked by the annotator, one of each kind the report has. The sample is purposive, not random. It is meant to cover page kinds, not to mirror how often each kind occurs.

**What does each instance consist of?**

- The source PDF and its SHA-256 hash, page count, title, document type, family, department, language, split and rights status (`data/<track>/documents/<id>.json`).
- Per labelled page: the Markdown reference, status (`marked`, `draft`, `checked`, `skip`), page kind, language, where the first draft came from, annotator, time of last change, notes, and the hash of the PDF the label belongs to (`data/<track>/annotations/<id>/page-NNN.json`).
- Per certificate, optionally: measurement records (element, value, unit, expanded uncertainty, coverage factor, status).

**Is there a label for each instance?** The transcription is the label. Pages without one are not part of the benchmark.

**Is anything missing from instances?** By rule the label leaves out running headers and footers, page numbers, logos, handwriting, signatures, stamps and text inside drawings. See the [annotation guide](annotation-guide.md).

**Are there recommended splits?** Planned: a split by report family into `dev` and `test`, so that two revisions of one report never fall on both sides. Not done yet. Every document is `dev` today.

**Are there errors, noise or redundancies?**

- All labels are drafts by one annotator and have not had their second check.
- Labels start from a model's draft, so they may carry that model's habits.
- Some public certificates are registered in both tracks and will be removed from the closed track.
- Reports of one family share layouts, so pages are not independent.

**Is the dataset self-contained?** Yes. Nothing is linked from outside.

**Does it contain confidential data?** The closed track consists of internal BAM reports and is confidential as a whole.

**Does it contain data about people?** Yes. Reports and certificates carry printed names, roles, signatures and contact details of staff and, in internal reports, possibly of customers or partners. Signatures and handwriting are left out of the labels. Printed names and contact lines are kept, because a faithful transcription needs them. On the open track these are names BAM has already published on its certificates.

## Collection process

**How was the data acquired?** Open track: certificates downloaded from BAM's public web pages for reference materials. Closed track: PDF reports supplied by **[fill in: source system or departments]** and copied onto the BAM GPU server by the data steward.

**Over what timeframe?** Collected in October and November 2026. The documents themselves date from **[fill in: range of years]**.

**Who was involved?** The data steward alone.

**Were the people whose names appear asked for consent?** No individual consent was sought. The documents were created in the course of BAM's work and are processed inside BAM for a research purpose. **[fill in after talking to the data protection officer: legal basis]**

## Preprocessing and labelling

**What was done to the raw data?** PDFs are kept unchanged and identified by hash. Pages are rendered to PNG on demand at the resolution a system card asks for.

**How were labels made?**

1. The annotator picks pages.
2. A first draft is produced by a model. Closed track: an open-weight model on the BAM GPU server, recorded per page. Open track: an AI assistant working from the page image and the Poppler text layer, with every number checked by program against the text layer and the two widest tables rebuilt from word positions.
3. The annotator corrects the draft against the page image.
4. A second check follows after at least two days. Only then does the status become `checked`.

**Is the raw data kept?** Yes. PDFs, every label version currently in use, and all model outputs per run.

**Is the labelling software available?** Yes, it is the annotation view of the dashboard in this repository.

## Uses

**What has it been used for?** Scoring 32 systems on the closed track (interim) and a text-layer baseline on the open track.

**What else could it be used for?** Choosing an extraction model for a BAM digitisation task. Regression testing when a model or a prompt changes. Studying how label drafting by a model biases later scores.

**What should it not be used for?**

- Training or fine-tuning models that are then scored on it.
- Claims about document types it does not contain.
- Ranking systems whose intervals overlap.
- Any use of the closed track outside BAM.

**Is there anything in its make-up that could affect future use?** The page sample over-represents tables on purpose. Scores are therefore not an estimate of average quality over a whole archive.

## Distribution

**How is it distributed?** Open track: in the Git repository. Closed track: not distributed. Its aggregate scores are published only when 20 or more pages back them.

**Under which licence?** Not decided. The software licence needs a decision under BAM's open source strategy. The public certificates are BAM publications; their `rights_status` is `public_access_confirmed_redistribution_permission_unverified` until BAM confirms that they may be redistributed.

**Are there third-party restrictions?** The closed track is under BAM's confidentiality rules and, where reports were written for customers, possibly under contract terms. **[fill in if known]**

## Maintenance

**Who maintains it?** The data steward. **[fill in: functional mailbox or team contact, and who takes over when the steward leaves; the BAM Code requires data to be handed over]**

**How are corrections handled?** A corrected label keeps its file and gets a new timestamp. `bambench rescore` recomputes all scores from the saved outputs. Changes that can move a score are listed in the [changelog](CHANGELOG.md).

**Will it be updated?** Yes: more closed-track pages until the label freeze, then versioned releases. A release fixes the set of `checked` pages and the scorer version.

**Will older versions stay available?** Git history keeps every state of the open track. Closed-track states should be deposited per release in the BAM Data Store.

**How long is it kept?** At least ten years after publication or the end of the project, as the BAM Data Policy requires.
