"""Model A denial reason classifier (lightweight keyword baseline)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

from appealpilot.domain import DenialClassification

TAXONOMY: Mapping[str, tuple[str, ...]] = {
    "medical_necessity": (
        "medical necessity",
        "not medically necessary",
        "insufficient clinical justification",
    ),
    "insufficient_documentation": (
        "insufficient documentation",
        "missing documentation",
        "records not provided",
        "documentation not submitted",
    ),
    "experimental_investigational": (
        "experimental",
        "investigational",
        "unproven",
    ),
    "out_of_network": (
        "out of network",
        "out-of-network",
        "non-participating provider",
    ),
    "authorization_procedural": (
        "prior authorization",
        "authorization required",
        "timely filing",
        "administrative denial",
    ),
}


def _score_terms(text: str, terms: tuple[str, ...]) -> tuple[int, tuple[str, ...]]:
    matched = []
    for term in terms:
        if re.search(re.escape(term), text, re.IGNORECASE):
            matched.append(term)
    return len(matched), tuple(matched)


def classify_denial_reason(denial_text: str) -> DenialClassification:
    """Classify denial reason into a v1 taxonomy."""

    best_category = "other"
    best_score = 0
    best_terms: tuple[str, ...] = ()

    for category, terms in TAXONOMY.items():
        score, matched = _score_terms(denial_text, terms)
        if score > best_score:
            best_category = category
            best_score = score
            best_terms = matched

    confidence = min(1.0, 0.35 + (0.2 * best_score)) if best_score > 0 else 0.3
    return DenialClassification(
        category=best_category,
        confidence=confidence,
        matched_terms=best_terms,
    )
