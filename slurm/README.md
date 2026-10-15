# Running on the shared Slurm GPU

1. On the login node (with internet), download weights once:

       export HF_HOME=/path/to/project/models
       huggingface-cli download Qwen/Qwen3.5-9B

2. Submit a run. The job starts vLLM on 127.0.0.1 inside the job, runs every annotated page,
   scores it and stops the server:

       export BAMBENCH_MODELS=/path/to/project/models
       sbatch slurm/serve_and_run.sbatch qwen3.5-9b open
       sbatch slurm/serve_and_run.sbatch qwen3.5-9b closed

3. Look at results in the dashboard (`python -m bambench serve`) through an SSH tunnel:

       ssh -L 8765:localhost:8765 <login-node>

Sizing on a shared card: models up to 9B fit in about 20 GB; Qwen3.6-27B needs the FP8
checkpoint and about 30 GB plus KV cache. Lower `BAMBENCH_GPU_UTIL` if the card is shared.
