#!/usr/bin/env bash
set -euo pipefail

# Download AppealPilot v1 external datasets into data/raw and data/external.
# Usage:
#   bash scripts/download_datasets.sh
#   bash scripts/download_datasets.sh --force

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_DIR="${ROOT_DIR}/data/raw"
EXTERNAL_DIR="${ROOT_DIR}/data/external/cms_appeals_guidance"
FORCE=0

if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
elif [[ $# -gt 0 ]]; then
  echo "Usage: bash scripts/download_datasets.sh [--force]" >&2
  exit 1
fi

mkdir -p \
  "${RAW_DIR}/tc_puf" \
  "${RAW_DIR}/prior_auth_wa" \
  "${RAW_DIR}/dfs_external_appeals" \
  "${EXTERNAL_DIR}"

download() {
  local url="$1"
  local dest="$2"

  if [[ -f "${dest}" && "${FORCE}" -ne 1 ]]; then
    echo "[skip] ${dest} already exists"
    return
  fi

  echo "[get] ${url}"
  curl -L --fail --retry 3 --retry-delay 2 "${url}" -o "${dest}"
}

download \
  "https://download.cms.gov/marketplace-puf/2026/transparency-in-coverage-puf.zip" \
  "${RAW_DIR}/tc_puf/transparency-in-coverage-puf-2026.zip"

download \
  "https://data.wa.gov/api/views/fysr-7kwx/rows.csv?accessType=DOWNLOAD" \
  "${RAW_DIR}/prior_auth_wa/wa_health_plan_prior_authorization_fysr-7kwx.csv"

download \
  "https://myportal.dfs.ny.gov/o/peasa/peasaserviceexcel" \
  "${RAW_DIR}/dfs_external_appeals/ny_dfs_external_appeals_all_years.xlsx"

download \
  "https://www.cms.gov/marketplace/about/affordable-care-act/external-appeals" \
  "${EXTERNAL_DIR}/cms_external_appeals.html"

download \
  "https://www.cms.gov/cciio/resources/fact-sheets-and-faqs/appeals06152012a" \
  "${EXTERNAL_DIR}/cms_appeals_fact_sheet.html"

download \
  "https://www.cms.gov/medicare/appeals-grievances/managed-care/reconsideration-advantage-health-plan-part-c" \
  "${EXTERNAL_DIR}/cms_part_c_reconsideration.html"

download \
  "https://www.cms.gov/medicare/appeals-and-grievances/mmcag/downloads/parts-c-and-d-enrollee-grievances-organization-coverage-determinations-and-appeals-guidance.pdf" \
  "${EXTERNAL_DIR}/parts-c-and-d-enrollee-grievances-organization-coverage-determinations-and-appeals-guidance.pdf"

echo "Done. Files available in:"
printf " - %s\n" \
  "${RAW_DIR}/tc_puf/transparency-in-coverage-puf-2026.zip" \
  "${RAW_DIR}/prior_auth_wa/wa_health_plan_prior_authorization_fysr-7kwx.csv" \
  "${RAW_DIR}/dfs_external_appeals/ny_dfs_external_appeals_all_years.xlsx" \
  "${EXTERNAL_DIR}/cms_external_appeals.html" \
  "${EXTERNAL_DIR}/cms_appeals_fact_sheet.html" \
  "${EXTERNAL_DIR}/cms_part_c_reconsideration.html" \
  "${EXTERNAL_DIR}/parts-c-and-d-enrollee-grievances-organization-coverage-determinations-and-appeals-guidance.pdf"
