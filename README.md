# appealpilot
Group Project for CIS568

## Model C (Provider-Swappable via aisuite)

Install dependencies:

```bash
pip install -r env/requirements.txt
```

Set provider API key(s):

```bash
export OPENAI_API_KEY="..."
export GROQ_API_KEY="..."  # optional, only needed for groq:* models
```

Generate a Model C packet:

```bash
PYTHONPATH=src python src/scripts/generate_model_c_packet.py \
  --case-json /path/to/case.json \
  --evidence-json /path/to/evidence.json
```

Switch providers by changing model string:

```bash
MODEL_C_MODEL=openai:gpt-5-mini
# or
MODEL_C_MODEL=groq:llama-3.3-70b-versatile
```

## Model B Retrieval Storage

RAG embeddings for the demo are stored in a local persistent Chroma collection:

- Vector store: `chroma`
- Persist dir: `data/interim/chroma`
- Config source: `src/smallbizpulse/config/settings.yaml`

## Git Hygiene

- `data/` is intentionally ignored and should not be committed.
- Install repo-managed hooks after clone:

```bash
bash scripts/install-git-hooks.sh
```

- A pre-commit hook blocks staged files larger than `25 MB`.
