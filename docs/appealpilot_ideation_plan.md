# AppealPilot v1: Build and Implementation Plan

## 1) What I'll Build
AppealPilot is an AI denial-appeal copilot for small to mid-sized outpatient specialty clinics.
It will convert denial paperwork into a complete, payer-ready appeal packet.

Core v1 outputs:
- Appeal letter draft grounded in chart facts and retrieved precedent.
- Evidence packet checklist + attachment index.
- Structured case summary (payer, CPT/HCPCS, diagnosis context, denial reason, deadlines, next steps).

## 2) v1 Scope (Intentionally Narrow)
To keep execution tight and defensible:
- One specialty segment (selected from high-denial, high-appeal-value areas).
- Top 10 CPT/HCPCS codes for that segment.
- Top 2-3 payers in one state.
- Denial appeals workflow only (not full RCM).

## 3) Target Users and Workflow
Users:
- Buyer: practice admin/clinic manager.
- Daily operator: billing/RCM denial staff.
- Clinical reviewer: provider signs off when needed.

End-to-end workflow:
1. Upload denial letter and relevant chart notes.
2. Auto-extract payer/service/denial rationale/deadline signals.
3. Classify denial type and urgency.
4. Show required evidence checklist and missing items.
5. Retrieve similar prior decisions and rationale patterns.
6. Generate letter + packet index with explicit citations.
7. Export to PDF/packet format for submission.

## 4) Product and System Architecture
Main components:
- Ingestion service for denial letters and chart docs.
- Case normalization layer to a canonical schema.
- Classification model for denial reason + urgency flags.
- Retrieval system (Chroma persistent local vector index over appeal decisions/policies).
- Grounded generation service for letters/checklists.
- Rules engine for payer workflow steps and deadlines.
- Audit/citation trail to support "no claim without source."

Canonical case schema includes:
- `case_id`, payer/plan, CPT/HCPCS, diagnosis context.
- Denial category, clinical facts, outcome labels where available.
- Rationale text, evidence references, deadlines.

## 5) Data Plan
Initial sources noted in your draft:
- CMS Transparency in Coverage public-use files.
- WA prior auth denial/appeal outcome data.
- NY DFS external appeal decisions.
- CMS appeals/process guidance.

Data pipeline:
1. Land raw files in source-specific folders.
2. Parse and clean text/tables into structured records.
3. Segment appeal decisions into request/denial/rationale/outcome sections.
4. Build labeled sets for classifier and retrieval relevance.
5. Maintain de-identification and privacy-safe handling for clinical text.

## 6) Model Plan
Model A (Classifier):
- Input: denial text.
- Output: denial category + urgency/deadline flags.
- Baseline: TF-IDF + logistic regression, then DistilBERT if needed.

Model B (Retriever):
- Input: case features + denial category.
- Output: top similar prior decisions/policy snippets.
- Storage: Chroma local persistent collection (`data/interim/chroma`) for demo simplicity.
- Method: embedding + vector search + metadata filters.

Model C (Generator):
- Input: structured case facts + retrieved evidence.
- Output: payer-ready appeal letter + citation-linked checklist.
- Runtime: `aisuite` model router for provider portability.
- Default foundation: `openai:gpt-5-mini`.
- Hot-swap option: switch to Groq by changing model string (example: `groq:llama-3.3-70b-versatile`).
- Guardrails: cite only provided/retrieved facts, surface missing data explicitly.

## 7) Evaluation Plan
Offline metrics:
- Structure completeness.
- Evidence coverage.
- Groundedness/citation traceability.
- Classification precision/recall/F1.
- Retrieval relevance@k.

Human review (30-case eval):
- "Would you submit this?" score.
- Critical omissions.
- Hallucination flag.
- Clarity/professionalism score.

## 8) Delivery Roadmap
Phase 1 (Weeks 1-2):
- Finalize wedge (specialty, codes, payers), case schema, ingestion skeleton.

Phase 2 (Weeks 3-4):
- Build normalization pipeline and baseline classifier/retriever.

Phase 3 (Weeks 5-6):
- Implement grounded letter generation, checklist logic, exports.

Phase 4 (Weeks 7-8):
- Run evaluation set, tighten guardrails, produce demo flow.

## 9) Business Positioning and Moat
Positioning:
- Workflow-native appeal layer that plugs into existing RCM tools.
- Not a full RCM replacement.

Monetization:
- SaaS subscription by claim volume or seats (e.g., $500-$2,000/month).

Compounding advantage:
- Payer-specific appeal playbook built from outcomes and usage.
- Higher switching costs via templates, process embedding, and historical performance loop.
