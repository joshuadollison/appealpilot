# AppealPilot Talking Points (Implementation-Filled Draft)

This version is populated with what is actually built in this repository today.

## Presentation Constraints

- 20 minutes presentation + 5 minutes Q&A + 5 minutes transition.
- Every team member speaks during the 20-minute presentation.
- Required but not presented slides: sources/AI disclosure and task ownership.

## Slide 1: Elevator Pitch (1.5 min)

- AppealPilot turns a denial letter plus chart notes into a payer-ready appeal packet in one workflow.
- Buyer: clinic admin or revenue cycle leader.
- User: billing/RCM staff and provider reviewer.
- Core promise: faster appeals with grounded citations and explicit missing-document callouts.
- Current built output artifacts:
  - `case_summary.json`
  - `classification.json`
  - `evidence_items.json`
  - `appeal_packet.json`
  - `appeal_letter.md`
  - `evidence_checklist.md`

## Slide 2: Current State and Pain (2 min)

- Today’s process is manual and fragmented:
  - read denial text,
  - interpret denial reason,
  - search for similar precedent,
  - draft letter from scratch,
  - assemble attachments.
- Pain points:
  - high admin time per appeal,
  - inconsistent quality across staff,
  - missing-evidence errors that weaken appeals,
  - low transparency on why language was used.
- AppealPilot’s focus is to compress this into one guided flow with machine-readable outputs.

## Slide 3: AI-Enabled Solution + v1 Scope (2 min)

- v1 workflow implemented:
  - parse denial text (`src/appealpilot/ingest/denial_parser.py`)
  - classify denial reason (`src/appealpilot/models/model_a_classifier.py`)
  - retrieve similar NY DFS cases from Chroma (`src/appealpilot/retrieval/chroma_retriever.py`)
  - generate appeal packet using `aisuite` Model C (`src/appealpilot/models/model_c_aisuite.py`)
  - export final packet and markdown artifacts (`src/appealpilot/workflow/appeal_pipeline.py`)
- In scope:
  - text-based denial + chart note input,
  - NY DFS external appeals retrieval corpus,
  - draft packet generation with citations/checklist.
- Out of scope:
  - direct EMR integration,
  - auto-submission to payer portals,
  - full RCM platform replacement.

## Slide 4: Industry Analysis (Five Forces + Trends) (2 min)

- Industry: denial management workflow tooling for outpatient clinics.
- Rivalry:
  - large RCM platforms and services include denial workflows but are broad and heavier to deploy.
- New entrants:
  - generic LLM wrappers are easy to build, but grounded workflow quality and trust are harder.
- Buyer power:
  - clinics are cost-sensitive and want measurable ROI quickly.
- Supplier power:
  - model/API providers influence cost and reliability.
- Substitutes:
  - manual Word template workflows,
  - outsourced billing/appeals services,
  - non-specialized AI chat tools.
- Trend tailwinds:
  - pressure on administrative costs,
  - broader AI adoption,
  - increasing expectation for fast cycle times.

## Slide 5: Competitive Advantage (1.5 min)

- Strategic choice: workflow-native copilot for appeals, not full revenue-cycle software.
- Deliberate tradeoffs:
  - narrow wedge first (denial appeals),
  - prioritize explainability and auditable outputs over broad feature sprawl.
- Value-chain fit in current build:
  - deterministic parsing and classification,
  - retrieval-grounded generation,
  - machine-readable output artifacts for downstream operations.

## Slide 6: Sustainable Advantage (Power Mechanisms) (1.5 min)

- Process power:
  - standardized packet structure and repeatable workflow.
- Switching costs:
  - team templates, operating process, and historical output library become embedded.
- Data/network effects (future state):
  - de-identified outcomes can refine payer-specific playbooks and retrieval prompts.
- Counter-positioning:
  - purpose-built appeal workflow can iterate faster than broad RCM suites.

## Slide 7: Business Model + Unit Economics (2 min)

- Proposed model: SaaS subscription by clinic size/claim volume.
- Value creation:
  - cut analyst time per appeal,
  - improve packet completeness and consistency.
- Cost drivers:
  - LLM inference (if cloud generation),
  - embedding/index compute,
  - onboarding and support.
- Practical cost controls already implemented:
  - default local retrieval embeddings: `sbert`,
  - local alternatives: `insurance_bert` and `hash`,
  - OpenAI embedding batching and per-input truncation guardrails to stay under token limits.

## Slide 8: System Design (2 min)

- Input:
  - denial letter text,
  - optional chart notes text.
- Model A:
  - keyword-taxonomy classifier with categories:
    - `medical_necessity`
    - `insufficient_documentation`
    - `experimental_investigational`
    - `out_of_network`
    - `authorization_procedural`
- Model B (RAG retrieval):
  - Chroma persistent collection at `data/interim/chroma`,
  - corpus loaded from `data/raw/dfs_external_appeals/ny_dfs_external_appeals_all_years.xlsx`,
  - retrieval returns top-k snippets + metadata + distances.
- Model C:
  - `aisuite` provider-router with model string portability (`openai:*` or `groq:*`),
  - default model in settings: `openai:gpt-5-mini`,
  - strict JSON output contract and grounding rules.
- Reliability behavior:
  - GPT-5 parameter compatibility handling (`max_completion_tokens`),
  - retry once if model returns empty content,
  - fallback to deterministic template generator on Model C response failure.

## Slide 9: Live Demo Plan (2.5 min)

- Demo surface: Streamlit dashboard (`dashboard/app/app.py`).
- Show 3 panels:
  - Vector store rebuild with provider selection and reset.
  - Run full appeal workflow.
  - LLM pass-through test panel for direct prompt sanity checks.
- Suggested live sequence:
  1. Rebuild vector store with `sbert` (or `insurance_bert` for domain demo).
  2. Run workflow on sample denial/chart notes.
  3. Show generated cover letter + detailed justification + checklist + citations.
  4. Open markdown artifacts and JSON artifacts in the new Artifact Explorer tabs.
  5. Show one failure mode: switch to template runtime or trigger fallback explanation.
- Concrete example from current output (`outputs/appeals/dashboard_20260214T004511Z`):
  - classification: `medical_necessity` with confidence `0.55`
  - top-k evidence returned: `5` cases
  - generated packet includes explicit `missing_information` and citation links.

## Slide 10: Go-To-Market Plan (1.5 min)

- Beachhead:
  - small-to-mid outpatient clinics with recurring denial volume and lean RCM teams.
- Land motion:
  - pilot with one specialty workflow and high-frequency denial patterns.
- Expand motion:
  - add payer-specific templates,
  - add additional denial categories and specialty playbooks,
  - integrate deeper into claim ops workflow.
- Partnerships (future):
  - RCM consultants,
  - specialty billing groups,
  - workflow tool integrations.

## Slide 11: AI Risks and Mitigations (1.5 min)

- Hallucination / unsupported claims:
  - grounding rule in prompt: use only provided facts/evidence,
  - citation structure required in output,
  - missing info explicitly surfaced.
- Empty or malformed model output:
  - guarded parsing with strict JSON contract,
  - retry path for GPT-5 empty-content responses,
  - fallback to template generator so workflow still returns a packet.
- Privacy/security:
  - local key file separation (`keys.local.yaml`) outside committed config,
  - no requirement to store PHI in repo data paths.
- Operational safety:
  - deterministic local embedding options (`hash`, `sbert`, `insurance_bert`) for offline/demo continuity.

## Slide 12: Ask, Milestones, Success Metrics (1.5 min)

- Ask:
  - sponsor a pilot cohort,
  - access to de-identified denial examples for evaluation,
  - 1 clinical reviewer + 1 RCM reviewer for rubric scoring.
- 30/60/90 plan:
  - 30 days: harden data normalization, build labeled eval set, baseline scorecard.
  - 60 days: tune retrieval relevance and prompt contracts by denial category.
  - 90 days: pilot with reviewer loop, compare manual vs assisted packet quality/time.
- Success metrics:
  - structure completeness rate,
  - citation-groundedness rate,
  - retrieval relevance@k,
  - reviewer “would submit” score,
  - median time-to-first-draft.

## Slide 13: Sources and AI Tool Disclosure (Required, Not Presented)

- Use `data/sources.md` as the baseline source inventory.
- Cite external data and policy references used in claims.
- Add explicit AI tool disclosure used by the team for ideation, drafting, coding, or analysis.

## Slide 14: Task Ownership (Required, Not Presented)

- Add a one-page table with no overlap in primary ownership:
  - product strategy and pitch narrative,
  - system architecture and implementation,
  - data sourcing and preprocessing,
  - demo build and demo backup video,
  - business model and GTM,
  - risk/compliance section and final deck QA.

## Optional Appendix (For Q&A)

- Retrieval configuration details from `src/appealpilot/config/settings.yaml`.
- API endpoint examples from `src/appealpilot/api/app.py`.
- Test coverage highlights from `src/tests/`.
- Backup screenshots of dashboard outputs and generated artifacts.
