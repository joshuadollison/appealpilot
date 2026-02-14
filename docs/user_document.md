# AppealPilot User Instructions

## 1) Purpose
AppealPilot is an end-to-end MVP that takes denial text and produces:
- structured case summary,
- denial classification,
- retrieved similar NY DFS appeal cases,
- generated appeal packet draft with checklist/citations.

## 2) Prerequisites
- Python 3.11+ recommended
- Run all commands from repo root: `appealpilot/`

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## 3) Fastest Run (Single Command Demo)

```bash
bash scripts/run_full_demo.sh
```

This runs:
1. retrieval index build (hash embeddings),
- from where? what options?
- what embedding model?
2. full denial-to-appeal workflow,
- what options?
3. exports output artifacts.

Output files:
- `outputs/appeals/demo_run/case_summary.json`
- `outputs/appeals/demo_run/classification.json`
- `outputs/appeals/demo_run/evidence_items.json`
- `outputs/appeals/demo_run/appeal_packet.json`
- `outputs/appeals/demo_run/appeal_letter.md`
- `outputs/appeals/demo_run/evidence_checklist.md`

## 4) Full CLI Workflow (Step-by-Step)

### A. Build / Refresh Retrieval Index

```bash
PYTHONPATH=src python src/scripts/build_retrieval_index.py \
  --embedding-provider hash \
  --reset \
  --limit 2000
```

Options:
- `--xlsx-path <path>`: alternate DFS source file.
- `--limit <n>`: max rows ingested.
- `--reset`: drop and recreate collection before ingest.
- `--embedding-provider {openai,hash,sbert,insurance_bert,local}`: choose embedding backend.
- `--collection-name <name>`: override collection.

### B. Query Retrieval Index

```bash
PYTHONPATH=src python src/scripts/query_retrieval_index.py \
  --embedding-provider hash \
  --query "lumbar MRI denied for medical necessity" \
  --top-k 5
```

Options:
- `--where-json '{"decision_year":"2024"}'`: metadata filter.
- `--top-k <n>`: number of results.
- `--collection-name <name>`: override collection.

### C. Run End-to-End Appeal Pipeline

```bash
PYTHONPATH=src python src/scripts/run_appeal_pipeline.py \
  --denial-text-file docs/examples/denial_sample.txt \
  --chart-notes-file docs/examples/chart_notes_sample.txt \
  --embedding-provider hash \
  --generation-runtime template \
  --top-k 5 \
  --output-dir outputs/appeals/manual_run
```

Required input:
- either `--denial-text` or `--denial-text-file`

Optional:
- `--chart-notes` or `--chart-notes-file`
- `--generation-runtime {auto,aisuite,template}`
- `--collection-name <name>`
- `--output-dir <path>`

## 5) API Mode

Start server:

```bash
PYTHONPATH=src python src/scripts/run_api.py --host 127.0.0.1 --port 8000
```

Open interactive docs:
- `http://127.0.0.1:8000/docs`

Endpoints:
- `GET /health`
- `POST /classify`
- `POST /generate`

## 6) LLM-Backed Generation (Model C via aisuite)

Set keys (as needed):

```bash
export OPENAI_API_KEY="..."
export GROQ_API_KEY="..."
```

Switch model provider:

```bash
MODEL_C_MODEL=openai:gpt-5-mini
# or
MODEL_C_MODEL=groq:llama-3.3-70b-versatile
```

Direct Model C call:

```bash
PYTHONPATH=src python src/scripts/generate_model_c_packet.py \
  --case-json /path/to/case.json \
  --evidence-json /path/to/evidence.json
```

## 7) Config Reference

Primary config file:
- `src/appealpilot/config/settings.yaml`

Key retrieval fields:
- `retrieval.vector_store`
- `retrieval.persist_directory`
- `retrieval.collection_name`
- `retrieval.embedding_model`
- `retrieval.embedding_provider`
- `retrieval.upsert_batch_size`
- `retrieval.openai_max_batch_tokens`
- `retrieval.openai_max_input_tokens`
- `retrieval.top_k`

For local semantic embeddings, set:
- `retrieval.embedding_provider: sbert`
- `retrieval.embedding_model: sbert:sentence-transformers/all-MiniLM-L6-v2`

Insurance-domain local demo preset:
- `retrieval.embedding_provider: insurance_bert`
- `retrieval.embedding_model: insurance_bert:llmware/industry-bert-insurance-v0.1`

Key generation fields:
- `model_c.model`
- `model_c.temperature`
- `model_c.max_tokens`
- `model_c.top_p`

## 8) Common Issues

### `ModuleNotFoundError`
Reinstall deps:

```bash
python -m pip install -r requirements.txt
```

### OpenAI/Groq auth errors
Set API keys and rerun:

```bash
export OPENAI_API_KEY="..."
export GROQ_API_KEY="..."
```

### No retrieval results
- Ensure index was built first.
- Increase `--limit` during index build.
- Remove old collection with `--reset` and rebuild.

### Git blocks large files
Install hooks:

```bash
bash scripts/install-git-hooks.sh
```

Data is intentionally local-only and ignored from git.
