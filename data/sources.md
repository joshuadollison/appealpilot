# Data Sources

## Description
This manifest records the external datasets and policy/guidance references used in AppealPilot v1.
It captures where each source came from, where it is stored locally, when it was retrieved, and what it is used for in the project.

## Intended Usage
- Use these sources for class-project research, workflow prototyping, and model/evaluation setup for denial appeals.
- Treat files in `data/raw` and `data/external` as source-of-truth inputs; create transformed artifacts in `data/interim` and `data/processed`.
- Use `data/raw` sources for targeting, retrieval corpus construction, and feature engineering.
- Use `data/external/cms_appeals_guidance` sources for rules, deadlines, and policy-aware workflow messaging.
- Refresh or rebuild local copies with `bash scripts/download_datasets.sh` (or `--force` to overwrite).

## Source Inventory

| Source | Local Path | URL | Retrieved (local time) | Format | Intended Usage |
|---|---|---|---|---|---|
| CMS Transparency in Coverage PUF (2026) | `data/raw/tc_puf/transparency-in-coverage-puf-2026.zip` | `https://download.cms.gov/marketplace-puf/2026/transparency-in-coverage-puf.zip` | 2026-02-13 07:46:20 MST | ZIP (contains XLSX) | Identify payer/plan-level opportunity and scope the v1 payer wedge. |
| WA Health Plan Prior Authorization Data | `data/raw/prior_auth_wa/wa_health_plan_prior_authorization_fysr-7kwx.csv` | `https://data.wa.gov/api/views/fysr-7kwx/rows.csv?accessType=DOWNLOAD` | 2026-02-13 07:46:20 MST | CSV | Select high-value CPT/HCPCS/service categories for the initial specialty focus. |
| NY DFS External Appeals Decisions (all years export) | `data/raw/dfs_external_appeals/ny_dfs_external_appeals_all_years.xlsx` | `https://myportal.dfs.ny.gov/o/peasa/peasaserviceexcel` | 2026-02-13 07:47:09 MST | XLSX | Build similar-case retrieval corpus and extract rationale/decision patterns for grounded letter generation. |
| CMS External Appeals page | `data/external/cms_appeals_guidance/cms_external_appeals.html` | `https://www.cms.gov/marketplace/about/affordable-care-act/external-appeals` | 2026-02-13 07:47:25 MST | HTML | Reference baseline federal external appeal process context for workflow copy and controls. |
| CMS Appeals fact sheet | `data/external/cms_appeals_guidance/cms_appeals_fact_sheet.html` | `https://www.cms.gov/cciio/resources/fact-sheets-and-faqs/appeals06152012a` | 2026-02-13 07:47:26 MST | HTML | Support user-facing help text and policy explainer content. |
| CMS Part C reconsideration page | `data/external/cms_appeals_guidance/cms_part_c_reconsideration.html` | `https://www.cms.gov/medicare/appeals-grievances/managed-care/reconsideration-advantage-health-plan-part-c` | 2026-02-13 07:47:26 MST | HTML | Capture deadline/timing rules and process states for appeals workflow logic. |
| CMS Parts C & D appeals guidance PDF | `data/external/cms_appeals_guidance/parts-c-and-d-enrollee-grievances-organization-coverage-determinations-and-appeals-guidance.pdf` | `https://www.cms.gov/medicare/appeals-and-grievances/mmcag/downloads/parts-c-and-d-enrollee-grievances-organization-coverage-determinations-and-appeals-guidance.pdf` | 2026-02-13 07:47:27 MST | PDF | Detailed policy reference for rule extraction and auditability of workflow recommendations. |
