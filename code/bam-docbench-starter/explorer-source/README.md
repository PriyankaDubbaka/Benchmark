# Results explorer source

This React/TypeScript explorer was built and displayed in Tasklet. It uses React 19 and DaisyUI/Tailwind supplied by that preview environment. These files preserve its source and the actual snapshot data; this folder is not a standalone, hosted public benchmark or a submission server. The evaluator in `../src` remains the authoritative scoring implementation.

`data.ts` is generated from `../results/pilot/metrics.json`, `../data/manifest.json` and the two draft gold-label files. It contains no fabricated model results. The source PDF is not embedded. For a public site, first clear data/branding rights, choose a normal frontend build/deployment environment, and replace the local pilot presentation with validated release results and submission governance.
