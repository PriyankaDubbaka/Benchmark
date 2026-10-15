# Closed track (confidential)

This folder holds the internal BAM reports and everything derived from them: PDFs, page
images, annotations, raw model outputs and per-page scores. Everything here except this
README is gitignored, and the pre-commit hook refuses to commit it.

Keep this folder on BAM storage only, for example a restricted project directory on the
Slurm cluster. Only aggregate summaries in `results/closed/` may leave it.

Add a report with the dashboard (Documents, Add a PDF) or:

    python -m bambench add /path/report.pdf --track closed --id dept-report-001 --department "3.3"
