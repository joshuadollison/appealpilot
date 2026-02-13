"""Core domain models for the AppealPilot MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ParsedDenial:
    """Structured fields extracted from a denial text."""

    raw_text: str
    payer: str | None
    cpt_hcpcs_codes: tuple[str, ...]
    denial_reason_text: str
    deadline_hints: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DenialClassification:
    """Model A output."""

    category: str
    confidence: float
    matched_terms: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EvidenceItem:
    """Model B retrieval output normalized for Model C."""

    source_id: str
    snippet: str
    metadata: Mapping[str, Any]
    distance: float | None


@dataclass(frozen=True)
class AppealPacket:
    """Final packet output returned by the workflow."""

    case_summary: Mapping[str, Any]
    classification: DenialClassification
    evidence_items: Sequence[EvidenceItem]
    generated_output: Mapping[str, Any]
