# appealpilot
Group Project for CIS568

## What This Is

AppealPilot is an end-to-end MVP that turns a denial into:
- a structured case summary,
- a denial category classification,
- retrieved similar cases from NY DFS,
- a generated appeal packet draft with citations/checklist.

## Quick Start (Single Command Demo)

From repo root:

```bash
python -m pip install -r requirements.txt
bash scripts/run_full_demo.sh
```

Demo outputs land in:
- `outputs/appeals/demo_run/case_summary.json`
- `outputs/appeals/demo_run/classification.json`
- `outputs/appeals/demo_run/evidence_items.json`
- `outputs/appeals/demo_run/appeal_packet.json`
- `outputs/appeals/demo_run/appeal_letter.md`
- `outputs/appeals/demo_run/evidence_checklist.md`

## Core Pipeline Commands

Build retrieval index (Model B):

```bash
PYTHONPATH=src python src/scripts/build_retrieval_index.py --embedding-provider hash --reset --limit 2000
```

Query retrieval index:

```bash
PYTHONPATH=src python src/scripts/query_retrieval_index.py \
  --embedding-provider hash \
  --query "lumbar MRI denied for medical necessity" \
  --top-k 5
```

Run end-to-end denial -> appeal workflow:

```bash
PYTHONPATH=src python src/scripts/run_appeal_pipeline.py \
  --denial-text-file docs/examples/denial_sample.txt \
  --chart-notes-file docs/examples/chart_notes_sample.txt \
  --embedding-provider hash \
  --generation-runtime template \
  --top-k 5
```

## API

Run FastAPI server:

```bash
PYTHONPATH=src python src/scripts/run_api.py --host 127.0.0.1 --port 8000
```

Then open:
- `http://127.0.0.1:8000/docs`

## LLM Generation (Model C via aisuite)

Set provider API key(s):

```bash
export OPENAI_API_KEY="..."
export GROQ_API_KEY="..."  # optional, only needed for groq:* models
```

Switch providers by changing model string:

```bash
MODEL_C_MODEL=openai:gpt-5-mini
# or
MODEL_C_MODEL=groq:llama-3.3-70b-versatile
```

Generate Model C output directly:

```bash
PYTHONPATH=src python src/scripts/generate_model_c_packet.py \
  --case-json /path/to/case.json \
  --evidence-json /path/to/evidence.json
```

## Git Hygiene

- `data/` is intentionally ignored and should not be committed.
- Install repo-managed hooks after clone:

```bash
bash scripts/install-git-hooks.sh
```

- A pre-commit hook blocks staged files larger than `25 MB`.
