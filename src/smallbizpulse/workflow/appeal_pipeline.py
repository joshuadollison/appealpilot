"""End-to-end denial-to-appeal orchestration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from smallbizpulse.domain import AppealPacket, EvidenceItem
from smallbizpulse.ingest import parse_denial_text
from smallbizpulse.models import (
    ModelCGenerator,
    TemplateModelCGenerator,
    build_model_c_config,
    classify_denial_reason,
)
from smallbizpulse.retrieval import ChromaRetriever, build_retrieval_config

ATTACHMENT_GUIDANCE: dict[str, tuple[str, ...]] = {
    "medical_necessity": (
        "Provider progress note",
        "Prior failed conservative therapy documentation",
        "Relevant imaging or diagnostic report",
    ),
    "insufficient_documentation": (
        "Complete chart notes for DOS",
        "Procedure order/referral",
        "Medical records index",
    ),
    "experimental_investigational": (
        "Peer-reviewed literature summary",
        "Clinical guideline citation",
        "Physician attestation",
    ),
    "authorization_procedural": (
        "Authorization request timeline",
        "Payer correspondence log",
        "Submission confirmation records",
    ),
}


@dataclass(frozen=True)
class AppealPipelineConfig:
    output_root: str = "outputs/appeals"
    top_k: int = 5
    generation_runtime: str = "auto"  # auto | aisuite | template


class AppealPipeline:
    """Orchestrates Model A + Model B + Model C."""

    def __init__(
        self,
        config: AppealPipelineConfig | None = None,
        retrieval_overrides: Mapping[str, Any] | None = None,
    ):
        self.config = config or AppealPipelineConfig()
        self.retrieval_config = build_retrieval_config(overrides=retrieval_overrides)
        self.retriever = ChromaRetriever(self.retrieval_config)

    def _build_query_text(
        self,
        denial_reason: str,
        denial_category: str,
        payer: str | None,
        codes: Sequence[str],
        chart_notes: str | None,
    ) -> str:
        components = [
            f"denial category: {denial_category}",
            f"denial reason: {denial_reason}",
        ]
        if payer:
            components.append(f"payer: {payer}")
        if codes:
            components.append(f"service codes: {' '.join(codes)}")
        if chart_notes:
            components.append(f"chart summary: {chart_notes[:500]}")
        return "\n".join(components)

    def _build_required_attachments(self, denial_category: str) -> tuple[str, ...]:
        return ATTACHMENT_GUIDANCE.get(
            denial_category,
            (
                "Provider note",
                "Denial letter copy",
                "Supporting clinical documentation",
            ),
        )

    def _normalize_evidence(self, raw_results: Sequence[Any]) -> list[EvidenceItem]:
        normalized: list[EvidenceItem] = []
        for result in raw_results:
            metadata = dict(result.metadata)
            source_id = metadata.get("case_number") or result.doc_id
            normalized.append(
                EvidenceItem(
                    source_id=str(source_id),
                    snippet=result.text[:1600],
                    metadata=metadata,
                    distance=result.distance,
                )
            )
        return normalized

    def _select_generator(self) -> Any:
        runtime = self.config.generation_runtime
        if runtime == "template":
            return TemplateModelCGenerator()
        if runtime == "aisuite":
            return ModelCGenerator()

        model_c_config = build_model_c_config()
        if model_c_config.provider in {"openai", "groq"}:
            key_name = (
                "OPENAI_API_KEY" if model_c_config.provider == "openai" else "GROQ_API_KEY"
            )
            if key_name in os.environ:
                return ModelCGenerator(config=model_c_config)
        return TemplateModelCGenerator()

    def run(
        self,
        denial_text: str,
        chart_notes: str | None = None,
        top_k: int | None = None,
        additional_instructions: str | None = None,
    ) -> AppealPacket:
        parsed = parse_denial_text(denial_text)
        classification = classify_denial_reason(parsed.denial_reason_text)

        query_text = self._build_query_text(
            denial_reason=parsed.denial_reason_text,
            denial_category=classification.category,
            payer=parsed.payer,
            codes=parsed.cpt_hcpcs_codes,
            chart_notes=chart_notes,
        )

        raw_results = self.retriever.query(
            query_text=query_text,
            top_k=top_k or self.config.top_k,
        )
        evidence_items = self._normalize_evidence(raw_results)
        attachments = self._build_required_attachments(classification.category)

        case_summary = {
            "payer": parsed.payer,
            "cpt_hcpcs_codes": list(parsed.cpt_hcpcs_codes),
            "denial_reason_text": parsed.denial_reason_text,
            "denial_category": classification.category,
            "classification_confidence": classification.confidence,
            "deadline_hints": list(parsed.deadline_hints),
            "chart_notes_excerpt": (chart_notes or "")[:2000],
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }

        generator = self._select_generator()
        generated = generator.generate(
            case_summary=case_summary,
            retrieved_evidence=[
                {
                    "source_id": item.source_id,
                    "snippet": item.snippet,
                    "metadata": dict(item.metadata),
                    "distance": item.distance,
                }
                for item in evidence_items
            ],
            required_attachments=attachments,
            additional_instructions=additional_instructions,
        )

        return AppealPacket(
            case_summary=case_summary,
            classification=classification,
            evidence_items=evidence_items,
            generated_output=generated,
        )

    def export_packet(self, packet: AppealPacket, output_dir: Path | None = None) -> Path:
        target_dir = output_dir or Path(self.config.output_root) / datetime.now(
            timezone.utc
        ).strftime("%Y%m%dT%H%M%SZ")
        target_dir.mkdir(parents=True, exist_ok=True)

        (target_dir / "case_summary.json").write_text(
            json.dumps(packet.case_summary, indent=2, ensure_ascii=True) + "\n"
        )
        (target_dir / "classification.json").write_text(
            json.dumps(
                {
                    "category": packet.classification.category,
                    "confidence": packet.classification.confidence,
                    "matched_terms": list(packet.classification.matched_terms),
                },
                indent=2,
                ensure_ascii=True,
            )
            + "\n"
        )
        (target_dir / "evidence_items.json").write_text(
            json.dumps(
                [
                    {
                        "source_id": item.source_id,
                        "distance": item.distance,
                        "metadata": dict(item.metadata),
                        "snippet": item.snippet,
                    }
                    for item in packet.evidence_items
                ],
                indent=2,
                ensure_ascii=True,
            )
            + "\n"
        )
        (target_dir / "appeal_packet.json").write_text(
            json.dumps(packet.generated_output, indent=2, ensure_ascii=True) + "\n"
        )

        generated = packet.generated_output.get("output", {})
        cover = generated.get("cover_letter", "")
        details = generated.get("detailed_justification", "")
        citations = generated.get("citations", [])
        checklist = generated.get("evidence_checklist", [])

        letter_lines = [
            "# Appeal Letter Draft",
            "",
            cover,
            "",
            "## Detailed Justification",
            "",
            details,
            "",
            "## Citations",
            "",
        ]
        for item in citations:
            claim = item.get("claim", "")
            source = item.get("source_id", "")
            excerpt = item.get("source_excerpt", "")
            letter_lines.append(f"- {claim} ({source})")
            if excerpt:
                letter_lines.append(f"  - {excerpt[:300]}")
        (target_dir / "appeal_letter.md").write_text("\n".join(letter_lines).strip() + "\n")

        checklist_lines = ["# Evidence Checklist", ""]
        for item in checklist:
            checklist_lines.append(
                f"- {item.get('item', '')}: {item.get('status', '')} ({item.get('notes', '')})"
            )
        (target_dir / "evidence_checklist.md").write_text(
            "\n".join(checklist_lines).strip() + "\n"
        )

        return target_dir


def run_pipeline_once(
    denial_text: str,
    chart_notes: str | None = None,
    top_k: int = 5,
    generation_runtime: str = "auto",
    output_dir: Path | None = None,
    retrieval_overrides: Mapping[str, Any] | None = None,
) -> tuple[AppealPacket, Path]:
    pipeline = AppealPipeline(
        config=AppealPipelineConfig(top_k=top_k, generation_runtime=generation_runtime),
        retrieval_overrides=retrieval_overrides,
    )
    packet = pipeline.run(denial_text=denial_text, chart_notes=chart_notes, top_k=top_k)
    export_dir = pipeline.export_packet(packet=packet, output_dir=output_dir)
    return packet, export_dir
