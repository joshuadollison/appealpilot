"""Offline template generator for Model C fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class TemplateGenerationConfig:
    provider: str = "template"
    model: str = "template:appealpacket-v1"


class TemplateModelCGenerator:
    """Deterministic template output when LLM runtime is unavailable."""

    def __init__(self, config: TemplateGenerationConfig | None = None):
        self.config = config or TemplateGenerationConfig()

    def generate(
        self,
        case_summary: Mapping[str, Any],
        retrieved_evidence: Sequence[Mapping[str, Any]],
        required_attachments: Sequence[str] | None = None,
        additional_instructions: str | None = None,
    ) -> dict[str, Any]:
        payer = case_summary.get("payer") or "Payer"
        denial_category = case_summary.get("denial_category", "other")
        codes = ", ".join(case_summary.get("cpt_hcpcs_codes", [])) or "N/A"
        evidence_items = list(retrieved_evidence)[:5]

        cover = (
            f"Re: Appeal of denial ({denial_category}) for {payer}. "
            f"Requested service codes: {codes}."
        )

        detailed = (
            "This appeal is submitted with supporting clinical documentation and "
            "prior comparable determinations. The denial should be overturned "
            "based on the enclosed facts and references."
        )

        checklist = []
        for item in required_attachments or []:
            checklist.append({"item": item, "status": "missing", "notes": "Confirm and attach."})

        citations = []
        for idx, item in enumerate(evidence_items, start=1):
            citations.append(
                {
                    "claim": f"Comparable precedent supports reconsideration (reference {idx}).",
                    "source_id": item.get("source_id", f"evidence_{idx}"),
                    "source_excerpt": item.get("snippet", "")[:500],
                }
            )

        output = {
            "cover_letter": cover,
            "detailed_justification": detailed,
            "evidence_checklist": checklist,
            "missing_information": [],
            "citations": citations,
        }

        if additional_instructions:
            output["detailed_justification"] += f" Additional instructions: {additional_instructions}"

        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "usage": {},
            "output": output,
            "raw_text": "",
        }
