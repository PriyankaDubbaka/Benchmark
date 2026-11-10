# Compliance checklist

Each rule the project has to follow, what it asks for, where the project stands and what is still to do. Status on 10 November 2026.

**How to read the Status column.** *Met*: there is evidence in the repository. *Partly*: work exists, something named in the last column is missing. *Open*: needs an action or a decision. *To confirm*: only a BAM office can settle it.

**What was checked against the source.** The BAM Code, the BAM Data Policy, the DFG Code and the DFG statement on generative models were read on 10 November 2026. The rows on the ALLEA Code, the AI Act, GDPR, the Horizon Europe template and FAIR4RS are written from general knowledge of those texts and should be read against the originals before they are quoted.

**This is not legal advice.** Rows marked *To confirm* belong to BAM's legal office, data protection officer or ombudspersons.

## 1. BAM rules

| Rule | What it asks | Status | Evidence | To do |
| --- | --- | --- | --- | --- |
| BAM Code §1 | Results checked for reproducibility; everything needed to repeat the work is archived | Partly | Outputs stored per run, `rescore`, 94 tests, [reproduction steps](project-documentation.md#13-how-to-reproduce) | Pin model revisions in the system cards |
| BAM Code §1 | Legal requirements and third-party contracts considered; approvals obtained | To confirm | [DMP section 6](data-management-plan.md#6-ethics-and-legal) | Confirm internal research use of customer reports |
| BAM Code §4 | Authors are people with a real contribution; smaller contributions go in the acknowledgement | Met | [Project documentation section 12](project-documentation.md#12-use-of-ai-tools), `CITATION.cff` | Agree the author list before any paper is drafted |
| BAM Code §5 | Every step from raw data to result documented and kept available | Partly | Project documentation, changelog, Git history, run folders | Closed-track selection criteria in the [datasheet](datasheet.md) |
| BAM Code §5 | Metadata complete enough for an outside expert to reproduce | Partly | Document manifests, label metadata, system cards, summaries | vLLM version and weights revision per run |
| BAM Code §5 | Datasets kept ten years from publication | Open | [DMP section 7](data-management-plan.md#7-retention-and-deletion) | Deposit in the BAM Data Store |
| BAM Code §5 | Software archived centrally, audit-proof, as documented source code | Open | Code is on a personal GitHub account | Move to BAM GitLab, deposit tagged releases |
| BAM Code §5 | Data handed over when staff leave | Open | | Name a successor |
| BAM Code §5 | Limits of the documentation explained | Met | [Limitations](project-documentation.md#9-limitations) | |
| BAM Data Policy §3 | Ethical, data protection and confidentiality matters checked before data is generated and published | To confirm | Safeguards in [section 4.4](project-documentation.md#44-safeguards-for-the-confidential-track) | Data protection officer |
| BAM Data Policy §4, §5 | A data management plan from the planning phase, kept current | Met | [data-management-plan.md](data-management-plan.md) | Fill the open fields |
| BAM Data Policy §4, §5 | BAM Data Store as the usual place of storage; local disks and cloud services only as short-term working storage | Open | Data is on the GPU server and on GitHub | Create the Data Store project |
| BAM Data Policy §4, §5 | Structured metadata, FAIR preparation, persistent identifier | Partly | JSON manifests with hashes | DOI per release |
| BAM Data Policy §4 | Open access to data under a free licence unless rights stand against it; data availability statement | Partly | Open track is separable from the closed one; statement drafted in the DMP | Licence, rights on the certificates |
| BAM Data Policy §4 | Deletion traceable and documented | Met | [DMP section 7](data-management-plan.md#7-retention-and-deletion) | |
| BAM open source strategy | Named by the Data Policy as the rule for software | To confirm | Not read; the text was not available | Read it and choose the licence |

## 2. DFG Code of Conduct

| Guideline | What it asks | Status | Evidence | To do |
| --- | --- | --- | --- | --- |
| 7 Cross-phase quality assurance | Each step done to the standard of the field; origin of data, software and materials disclosed; public source code persistent, citable, documented | Partly | Tests, pre-merge review, system cards with sources, `CITATION.cff` | Second annotator on a sample; DOI |
| 9 Research design | State of research taken into account | Met | [Comparison with other benchmarks](gap-analysis-and-roadmap.md#1-how-it-compares) | |
| 10 Legal and ethical frameworks, usage rights | Legal duties and contracts respected; usage rights to data and results agreed and documented early | To confirm | DMP section 6 | Written agreement on who may use the corpus and the results |
| 11 Methods and standards | Sound, appropriate methods; for new methods, attention to quality assurance and standards | Met | Established metrics (edit distance, TEDS), bootstrap intervals, scorer version in every summary | Validate the Numbers score on hand-checked pages |
| 12 Documentation | All information relevant to a result documented so it can be reviewed; results that do not support the expectation included; no selection of results; documentation protected against manipulation | Partly | Project documentation, limitations, failed models kept on the leaderboard, Git history | Protected branch and signed tags in BAM GitLab |
| 13 Public access | Results made available; data, methods and software provided where possible, following FAIR; own software published with source code and a licence | Open | Hosted dashboard prepared | Licence, release, move to BAM GitLab |
| 14 Authorship | Genuine, identifiable contribution; all authors agree on the final version | Met | Section 12 of the project documentation | |
| 17 Archiving | Data, materials and software kept for an appropriate period, generally ten years, at the institution or in a repository | Open | DMP section 7 | BAM Data Store |

## 3. Use of AI tools

| Rule | What it asks | Status | Evidence | To do |
| --- | --- | --- | --- | --- |
| DFG statement on generative models, September 2023 | Disclose whether generative models were used, which, for what purpose and to what extent | Met once confirmed | [Project documentation section 12](project-documentation.md#12-use-of-ai-tools); label metadata records the source of each first draft | The author reads and confirms section 12 |
| Same | Only natural persons can be authors; the researcher stays responsible for content | Met | Section 12 | |
| Same | No infringement of others' rights through the use of such tools | Met | Confidential documents were never given to an external tool | Keep cloud assistants away from folders that hold `data/closed/` |
| Same | The statement carries a note that it was revised in December 2025 | To confirm | | Read the current version |
| ALLEA European Code of Conduct for Research Integrity, 2023 edition | Honest reporting of methods, including the use of AI and automated tools | Met once confirmed | Section 12 | Read against the original |

## 4. Data protection and law

| Rule | What it asks | Status | Evidence | To do |
| --- | --- | --- | --- | --- |
| GDPR and BDSG | A legal basis for processing personal data; data minimisation; security | To confirm | Processing stays inside BAM; signatures and handwriting left out of labels; access limited | Data protection officer; entry in BAM's record of processing if required |
| Confidentiality of internal reports | No disclosure outside BAM | Met | Section 4.4; no closed file in Git history (`git log --all --name-only -- data/closed` lists only the README) | Check again before every push to a new remote |
| Model licences | Use within the terms of each licence | Partly | Licence on every system card; EU-excluded models kept out; watchlist with reasons | Legal review; clear the three cards that say "verify" |
| Regulation (EU) 2024/1689, AI Act | Duties depend on role and use. Research and evaluation of models is one situation, productive use of a model inside BAM another | To confirm | Models run locally; BAM publishes none of them | Ask the legal office before a model goes into productive use |
| Copyright in the public certificates | Right to redistribute | Open | `rights_status` field on every manifest | Ask the BAM unit that publishes the certificates |

## 5. Standards for the benchmark itself

| Standard | What it asks | Status | Evidence | To do |
| --- | --- | --- | --- | --- |
| FAIR, findable | Identifiers and rich metadata | Partly | IDs, hashes, manifests | DOI |
| FAIR, accessible | Retrievable by identifier; metadata stay available | Partly | Git, hosted dashboard prepared | BAM GitLab, Data Store |
| FAIR, interoperable | Open formats and shared vocabularies | Met | JSON, Markdown, HTML tables, LaTeX; conventions of OmniDocBench | |
| FAIR, reusable | Licence and provenance | Partly | Provenance per label | Licence |
| FAIR4RS | Software citable, versioned, licensed, documented | Partly | `CITATION.cff`, changelog, tests, documentation | Licence, release tag, DOI |
| Datasheets for Datasets | Motivation, composition, collection, labelling, uses, distribution, maintenance | Partly | [datasheet.md](datasheet.md) | Fill the closed-track fields |
| BetterBench, design | Capability defined, real-world relevance, metrics explained, floor and ceiling | Partly | Sections 1 and 2; text-layer floor | Human ceiling from a second annotator |
| BetterBench, implementation | Working code, script that reproduces published numbers, local models supported | Met | `run`, `rescore`, Slurm job | |
| BetterBench, documentation | Construction process, limits, statistical uncertainty reported, licence | Partly | This documentation; intervals on every score | Licence |
| BetterBench, maintenance | Contact, feedback channel, upkeep | Open | | Functional contact; issue tracker in BAM GitLab |

## 6. The seven decisions only BAM can take

1. Software and label licence.
2. Repository on BAM GitLab instead of a personal GitHub account.
3. Deposit in the BAM Data Store.
4. Data protection review.
5. Use of customer reports for internal research.
6. Redistribution of the public certificates.
7. Legal review of the model licences.
