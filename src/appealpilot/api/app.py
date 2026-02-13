"""FastAPI app for the AppealPilot MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from appealpilot.ingest import parse_denial_text
from appealpilot.models import classify_denial_reason
from appealpilot.workflow import run_pipeline_once


class ClassifyRequest(BaseModel):
    denial_text: str = Field(min_length=1)


class GenerateRequest(BaseModel):
    denial_text: str = Field(min_length=1)
    chart_notes: str = ""
    top_k: int = Field(default=5, ge=1, le=20)
    generation_runtime: str = Field(default="auto")
    embedding_provider: str | None = None
    collection_name: str | None = None
    output_dir: str | None = None


app = FastAPI(title="AppealPilot API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/classify")
def classify(request: ClassifyRequest) -> dict[str, Any]:
    parsed = parse_denial_text(request.denial_text)
    classified = classify_denial_reason(parsed.denial_reason_text)
    return {
        "payer": parsed.payer,
        "codes": list(parsed.cpt_hcpcs_codes),
        "deadline_hints": list(parsed.deadline_hints),
        "classification": {
            "category": classified.category,
            "confidence": classified.confidence,
            "matched_terms": list(classified.matched_terms),
        },
    }


@app.post("/generate")
def generate(request: GenerateRequest) -> dict[str, Any]:
    retrieval_overrides = {}
    if request.embedding_provider:
        retrieval_overrides["embedding_provider"] = request.embedding_provider
    if request.collection_name:
        retrieval_overrides["collection_name"] = request.collection_name

    output_dir = Path(request.output_dir) if request.output_dir else None
    packet, export_dir = run_pipeline_once(
        denial_text=request.denial_text,
        chart_notes=request.chart_notes,
        top_k=request.top_k,
        generation_runtime=request.generation_runtime,
        output_dir=output_dir,
        retrieval_overrides=retrieval_overrides or None,
    )

    return {
        "export_dir": str(export_dir),
        "classification": {
            "category": packet.classification.category,
            "confidence": packet.classification.confidence,
            "matched_terms": list(packet.classification.matched_terms),
        },
        "evidence_count": len(packet.evidence_items),
        "generator_provider": packet.generated_output.get("provider"),
        "generator_model": packet.generated_output.get("model"),
    }
