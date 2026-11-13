# Data management plan: BAM Extraction Benchmark (PW2)

The BAM Data Policy asks for a data management plan for every project, started during planning and kept current as a living document. This plan uses the section order of the Horizon Europe template, which covers the same ground. If BAM prescribes its own template, move the content into it. Version of 10 November 2026. Fields marked **[fill in]** or **[decide]** are open.

| | |
| --- | --- |
| Project | PW2, extraction benchmark |
| Data steward | Priyanka Dubbaka |
| Responsible at management level | **[fill in]** |
| Review of this plan | at the label freeze, at each release, and when the steward changes |

## 1. Data summary

| Data | Format | Volume | Origin | Confidential |
| --- | --- | --- | --- | --- |
| Public certificates | PDF | 5 files, 21 pages | BAM public web pages | no |
| Internal reports | PDF | 54 files, **[fill in]** pages, about 125 MB as delivered | **[fill in]** | yes |
| Document manifests | JSON | one small file per document | written by the software | closed track: yes |
| Reference labels | JSON holding Markdown | one file per labelled page | model draft corrected by the annotator | closed track: yes |
| System cards | JSON | 39 files | written from the model cards of the publishers | no |
| Model outputs | Markdown and JSON per page and run | a few MB per run | produced on the BAM GPU server | closed track: yes |
| Score summaries | JSON | one file per system and track | computed by the scorer | closed track: only aggregates, and only with 20 or more pages |
| Source code and documentation | Python, JavaScript, Markdown | under 1 MB | written in this project | no |
| Model weights | publisher formats | 1 to 30 GB per model | downloaded from Hugging Face | no; third-party property, not project data |

Purpose: to evaluate document extraction systems for BAM. Reuse of existing data: the public certificates and the internal reports already existed; nothing was collected from people.

## 2. FAIR data

### Findable

- Every document has a stable `document_id` and the SHA-256 hash of its PDF. A label records the hash it belongs to, so a label can never be applied to another revision by mistake.
- Every run has an identifier built from its start time. Every summary records the software version, the scorer version and the system card used.
- **[decide]** A persistent identifier (DOI) for each release. The open track and the software can receive one from a public repository once rights and licence are settled. The closed track receives a BAM Data Store identifier.

### Accessible

- Open track and software: Git repository. Today it is on a personal GitHub account. **[decide]** Move to BAM GitLab, which the BAM Data Policy points to for primary storage.
- Closed track: BAM GPU server, access limited to the steward. **[fill in: who else has access to the account and the backup]**
- A read-only dashboard can be published with GitLab Pages for BAM staff. It carries no confidential content. See [hosting-on-gitlab.md](hosting-on-gitlab.md).
- A data availability statement for any publication: *The public track and all software are available at [identifier]. The internal track consists of confidential BAM reports and cannot be shared. Its aggregate results are included.*

### Interoperable

- Open formats only: PDF, PNG, JSON, Markdown with HTML tables, LaTeX for formulas.
- The reference format follows the conventions of OmniDocBench, so labels can be converted for other scorers.
- Metadata fields per document: title, type, family, department, language, split, rights status, date added.

### Reusable

- Labelling rules: [annotation-guide.md](annotation-guide.md). Dataset description: [datasheet.md](datasheet.md).
- Licence for software and for the open-track labels: **[decide]**. Until then nobody outside BAM has a right to reuse them.
- Provenance per label: annotator, source of the first draft, time of last change, status.

## 3. Other research outputs

- **Software.** The benchmark package, its tests and the dashboard. The BAM Code asks for source code to be archived centrally in an audit-proof way with sufficient documentation. Action: tag each release in Git and deposit the tagged state in the BAM Data Store.
- **System cards.** They are part of the method and are versioned with the code.
- **Reports and slides.** Stored with the project documents. **[fill in: location]**

## 4. Allocation of resources

- Labelling: one person, about 15 pages a week.
- Computing: slices of one A100 80 GB on the shared BAM GPU server. A full pass of all systems over 60 pages takes a few GPU hours.
- Storage: under 1 GB for data and outputs. Model weights take a few hundred GB and can be downloaded again, so they need no backup.
- Long-term preservation: BAM Data Store, no project cost.

## 5. Data security

| Risk | Measure |
| --- | --- |
| A confidential file is committed to Git | `data/closed/` is ignored; a commit hook refuses files from it. The hook must be switched on once per clone with `git config core.hooksPath .githooks`. |
| A page is sent to an external service | Model endpoints must be local or explicitly allowed. Vendor cloud modes are switched off and outbound proxies are disabled for those tools. The GPU nodes have no internet access. |
| Someone reaches the local dashboard through a browser | It binds to localhost, checks the Host header and refuses cross-site writes. |
| Scores reveal content | Closed-track scores are exported only as aggregates over 20 or more pages. |
| The hosted copy leaks | It is built only from committed, published results and contains no closed document names, text, images or outputs. |
| Loss of labels | **[fill in: backup of the server's home directory, or a regular copy to the BAM Data Store]**. Labels are the most expensive data in the project and exist in one place today. |
| Use of AI coding assistants on the server | Never start a cloud-connected assistant in a folder that contains `data/closed/`. Use a clone without the closed data. |

## 6. Ethics and legal

- **Personal data.** Reports carry names, roles and signatures. Processing stays inside BAM. Labels leave out signatures and handwriting. Action: describe the processing to BAM's data protection officer and record the legal basis. **[fill in]**
- **Third-party rights.** Reports written for customers may be under contract terms. Action: confirm that internal research use is covered. **[fill in]**
- **Public certificates.** Publicly accessible. Permission to redistribute them in a public repository is not yet confirmed. Until then the repository must not be made public beyond its current state. **[decide]**
- **Model licences.** Read from each model card. Models whose licence excludes the EU are not used. Legal review by BAM is pending. **[decide]**
- **AI Act.** The benchmark is a research activity that evaluates models. Whether later productive use of a chosen model inside BAM brings duties under Regulation (EU) 2024/1689 is a question for BAM's legal office.

## 7. Retention and deletion

- Kept for at least ten years after publication or the end of the project: PDFs of both tracks, labels, system cards, outputs of the runs that back published numbers, summaries, the tagged software.
- May be deleted earlier: outputs of test runs, rendered page images, model weights.
- Deletion is documented, as the BAM Data Policy requires.
- When the steward leaves BAM, the data is handed over. **[fill in: to whom]**

## 8. Open actions

1. Decide the licence. **[decide]**
2. Create the project in BAM GitLab and push the repository.
3. Create the project in the BAM Data Store and deposit the closed track and the first release.
4. Arrange a backup for the labels before the freeze.
5. Talk to the data protection officer.
6. Confirm redistribution of the public certificates.
7. Name the person at management level who is responsible, and the successor for the data.
