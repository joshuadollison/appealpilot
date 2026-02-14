# AppealPilot Quick Start

This is the fastest path for someone who just cloned the repo.

## 1) Clone and enter project

```bash
git clone <your-repo-url> appealpilot
cd appealpilot
```

## 2) Create environment and install dependencies

Option A (recommended: conda):

```bash
conda env create -f env/environment.yml
conda activate appealpilot
```

Option B (pip only):

```bash
python -m pip install -r requirements.txt
```

## 3) Install git hooks (recommended)

```bash
bash scripts/install-git-hooks.sh
```

This enables the repo pre-commit hook that blocks files larger than 25 MB.

## 4) Download datasets (local only)

```bash
bash scripts/download_datasets.sh
```

Notes:
- Data is stored under `data/` and is intentionally gitignored.
- Re-run with `--force` to overwrite existing files.

## 5) Configure API keys (optional, only if using cloud models)

Copy the example file and fill in keys if needed:

```bash
cp src/appealpilot/config/keys.example.yaml src/appealpilot/config/keys.local.yaml
```

`keys.local.yaml` is separate from app settings and is ignored by git.

## 6) Run the one-command demo

```bash
bash scripts/run_full_demo.sh
```

Artifacts are written to:
- `outputs/appeals/demo_run/case_summary.json`
- `outputs/appeals/demo_run/classification.json`
- `outputs/appeals/demo_run/evidence_items.json`
- `outputs/appeals/demo_run/appeal_packet.json`
- `outputs/appeals/demo_run/appeal_letter.md`
- `outputs/appeals/demo_run/evidence_checklist.md`

## 7) Launch the dashboard

```bash
PYTHONPATH=src python src/scripts/run_dashboard.py --host 127.0.0.1 --port 8501
```

Open:
- `http://127.0.0.1:8501`

From the dashboard you can:
- rebuild the vector store,
- run the full workflow,
- inspect generated markdown/json artifacts,
- test direct LLM pass-through prompts.

## 8) Useful model/provider defaults

- Default retrieval embedding provider is `sbert` in `src/appealpilot/config/settings.yaml`.
- Other retrieval options include `insurance_bert`, `hash`, and `openai`.
- Model C provider/model can be changed in `src/appealpilot/config/settings.yaml` under `model_c`.
