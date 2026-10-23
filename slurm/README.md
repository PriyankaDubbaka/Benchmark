# Running on the shared Slurm GPU

1. Once, on the login node (it needs internet for this step only), install vLLM and download
   the weights:

       python3 -m venv ~/venvs/bam && source ~/venvs/bam/bin/activate
       pip install vllm
       export HF_HOME=$HOME/models
       hf download Qwen/Qwen3.5-9B

   Older versions of `huggingface_hub` call the command `huggingface-cli download`.

2. Submit from the repository folder, with the environment active. The job starts vLLM on
   127.0.0.1 inside the job, runs the system, and stops the server:

       source ~/venvs/bam/bin/activate
       cd ~/Benchmark
       export BAMBENCH_MODELS=$HOME/models
       sbatch --gres=gpu:4g.40gb:1 slurm/serve_and_run.sbatch qwen3.5-9b closed --draft-only

   `--draft-only` writes first drafts for every picked page and scores nothing; correct the
   drafts in the dashboard. Leave it out to score a system against the annotated pages.

3. Check the job with `squeue -u $USER` and its log with `tail bambench-<jobid>.out`. The
   log holds document names and timings only.

4. Look at results in the dashboard (`python3 -m bambench serve --port 8880`, outside the
   job) through an SSH tunnel from your own machine:

       ssh -L 8880:localhost:8880 <login-node>

## Sizing

The A100 cards on the shared node are split into MIG slices: one 40 GB (`4g.40gb`) and two 20 GB per A100.
`scontrol show node <node> | grep -i gres` lists the names. A slice that is too small fails
when vLLM loads the weights.

| System | Weights | Slice |
| --- | --- | --- |
| Granite-Docling-258M | 0.5 GB | 20 GB (download with `--revision untied`) |
| PaddleOCR-VL 1.5 and 1.6, GLM-OCR, MinerU2.5-Pro | about 2 GB | 20 GB |
| DeepSeek-OCR 2, dots.mocr | 6 to 7 GB | 20 GB |
| Qwen3-VL-8B | 17.5 GB | 40 GB |
| Qwen3.5-9B | 19 GB | 40 GB |
| Qwen3.6-27B-FP8 | about 30 GB | 40 GB, short context |

PaddleOCR-VL 1.6 and MinerU2.5-Pro also need their client package in the environment
(`paddleocr[doc-parser]`, `mineru-vl-utils[vllm]`) and their layout model downloaded once on
the login node, because the job runs offline.

Lower `BAMBENCH_GPU_UTIL` if the slice is shared. The job asks for 2 CPU cores and 32 GB of
memory, which fits the per-job limit on the shared partition; raise them with `sbatch
--cpus-per-task` and `--mem` if your account allows more.
