#!/bin/bash
# Start a local vLLM server for one system card, run the benchmark against it, then stop.
# Usage: sbatch slurm/serve_and_run.sbatch <system-id> <open|closed> [--draft-only]
#   Submit from the repository folder. On a MIG-partitioned card, ask for a slice that fits the
#   model, e.g. sbatch --gres=gpu:4g.40gb:1 slurm/serve_and_run.sbatch qwen3.5-9b closed --draft-only
#
# Adjust the partition, GPU request and module lines to your cluster. Compute nodes should
# have no outbound network: download weights once into $BAMBENCH_MODELS on the login node.
#SBATCH --job-name=bambench
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=%x-%j.out

set -euo pipefail
SYSTEM="${1:?system id, e.g. qwen3.5-9b}"
TRACK="${2:-open}"
EXTRA="${3:-}"   # --draft-only to write first drafts for picked pages without scoring
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/..}"

# module load cuda  # if your cluster needs it
# source .venv/bin/activate

export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # never reach out to the internet from here
export HF_HOME="${BAMBENCH_MODELS:-$HOME/models}"
PORT=$((8000 + SLURM_JOB_ID % 1000))
export BAMBENCH_VLLM_URL="http://127.0.0.1:${PORT}/v1"

SERVE=$(python3 -c "import json,sys; c=json.load(open('systems/${SYSTEM}.json')); print(c.get('serve',''))")
if [ -n "$SERVE" ]; then
  echo "starting: $SERVE --port $PORT --host 127.0.0.1"
  $SERVE --port "$PORT" --host 127.0.0.1 --gpu-memory-utilization "${BAMBENCH_GPU_UTIL:-0.85}" &
  VLLM_PID=$!
  trap 'kill $VLLM_PID 2>/dev/null || true' EXIT
  for i in $(seq 1 120); do
    curl -sf "http://127.0.0.1:${PORT}/v1/models" >/dev/null && break
    sleep 5
  done
fi

nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv || true
python3 -m bambench run "$SYSTEM" --track "$TRACK" $EXTRA
