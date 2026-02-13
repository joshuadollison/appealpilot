#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f "docs/examples/denial_sample.txt" ]]; then
  echo "ERROR: docs/examples/denial_sample.txt not found." >&2
  exit 1
fi

echo "[1/3] Building retrieval index (hash embeddings, demo mode)..."
PYTHONPATH=src python src/scripts/build_retrieval_index.py \
  --embedding-provider hash \
  --reset \
  --limit 500

echo "[2/3] Running end-to-end appeal pipeline..."
PYTHONPATH=src python src/scripts/run_appeal_pipeline.py \
  --denial-text-file docs/examples/denial_sample.txt \
  --chart-notes-file docs/examples/chart_notes_sample.txt \
  --embedding-provider hash \
  --generation-runtime template \
  --top-k 5 \
  --output-dir outputs/appeals/demo_run

echo "[3/3] Done."
echo "Artifacts:"
echo "  outputs/appeals/demo_run/case_summary.json"
echo "  outputs/appeals/demo_run/classification.json"
echo "  outputs/appeals/demo_run/evidence_items.json"
echo "  outputs/appeals/demo_run/appeal_packet.json"
echo "  outputs/appeals/demo_run/appeal_letter.md"
echo "  outputs/appeals/demo_run/evidence_checklist.md"
