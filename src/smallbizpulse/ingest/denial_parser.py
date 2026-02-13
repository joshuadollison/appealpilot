"""Denial text parser for the AppealPilot MVP."""

from __future__ import annotations

import re
from typing import Iterable

from smallbizpulse.domain import ParsedDenial

KNOWN_PAYERS = (
    "Aetna",
    "UnitedHealthcare",
    "Blue Cross",
    "Blue Shield",
    "Cigna",
    "Humana",
    "Anthem",
    "Healthfirst",
    "Fidelis",
    "Empire",
)

CPT_PATTERN = re.compile(r"\b\d{5}\b")
HCPCS_PATTERN = re.compile(r"\b[A-Z]\d{4}\b")
DEADLINE_PATTERN = re.compile(
    r"\b(?:within\s+\d+\s+days|deadline\s*[:\-]\s*[A-Za-z0-9,\-/ ]+)\b",
    re.IGNORECASE,
)
DENIAL_REASON_PATTERN = re.compile(
    r"(?:denial reason|reason for denial)\s*[:\-]\s*(.+)",
    re.IGNORECASE,
)


def _first_payer_match(text: str, payers: Iterable[str]) -> str | None:
    lowered = text.lower()
    for payer in payers:
        if payer.lower() in lowered:
            return payer
    return None


def parse_denial_text(raw_text: str) -> ParsedDenial:
    """Extract key structured fields from denial text."""

    text = raw_text.strip()
    payer = _first_payer_match(text, KNOWN_PAYERS)
    cpt_codes = set(CPT_PATTERN.findall(text))
    hcpcs_codes = set(HCPCS_PATTERN.findall(text))
    codes = sorted(cpt_codes | hcpcs_codes)

    reason_match = DENIAL_REASON_PATTERN.search(text)
    denial_reason_text = reason_match.group(1).strip() if reason_match else text[:400]
    deadline_hints = tuple(dict.fromkeys(match.group(0).strip() for match in DEADLINE_PATTERN.finditer(text)))

    return ParsedDenial(
        raw_text=text,
        payer=payer,
        cpt_hcpcs_codes=tuple(codes),
        denial_reason_text=denial_reason_text,
        deadline_hints=deadline_hints,
    )
