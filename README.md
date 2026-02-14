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

Local semantic option (recommended local quality/speed tradeoff):

```bash
PYTHONPATH=src python src/scripts/build_retrieval_index.py --embedding-provider sbert --reset --limit 2000
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

## Dashboard (Real-Time UI)

Start dashboard:

```bash
PYTHONPATH=src python src/scripts/run_dashboard.py --host 127.0.0.1 --port 8501
```

Then open:
- `http://127.0.0.1:8501`

Dashboard features:
- Rebuild vector store (button) with provider/limit/reset controls.
- Run full denial-to-appeal workflow interactively.
- Inspect classification, retrieved evidence, generated output, and exported file paths.

## Retrieval Embedding Providers

- `hash`: lightweight deterministic baseline, fully offline.
- `sbert` / `local`: local semantic embeddings via `sentence-transformers` (default model: `sentence-transformers/all-MiniLM-L6-v2`).
- `openai`: cloud embeddings via `text-embedding-3-small`.

OpenAI upserts are automatically token-batched to avoid request token limits during large index rebuilds.
To set a specific local model, set `retrieval.embedding_model` to `sbert:<model_name>`.

## LLM Generation (Model C via aisuite)

Set provider API key(s):

```bash
export OPENAI_API_KEY="..."
export GROQ_API_KEY="..."  # optional, only needed for groq:* models
```

or local-only config file:
- copy `src/appealpilot/config/keys.example.yaml`
- create `src/appealpilot/config/keys.local.yaml`
- fill keys there (gitignored by default)

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
