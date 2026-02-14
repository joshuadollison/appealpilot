from __future__ import annotations

from pathlib import Path

from appealpilot.models import ModelCResponseError
from appealpilot.workflow.appeal_pipeline import AppealPipeline, AppealPipelineConfig
from appealpilot.workflow import run_pipeline_once


def test_pipeline_runs_and_exports(tmp_path: Path) -> None:
    denial_text = """
    Payer: Aetna
    Denial Reason: Not medically necessary.
    CPT: 72148
    """
    output_dir = tmp_path / "packet"

    packet, exported = run_pipeline_once(
        denial_text=denial_text,
        chart_notes="Patient failed conservative therapy and reports persistent radicular pain.",
        top_k=2,
        generation_runtime="template",
        output_dir=output_dir,
        retrieval_overrides={
            "persist_directory": str(tmp_path / "chroma"),
            "collection_name": "pipeline_test_collection",
            "embedding_provider": "hash",
        },
    )

    assert exported == output_dir
    assert packet.classification.category in {"medical_necessity", "other"}
    assert (output_dir / "case_summary.json").exists()
    assert (output_dir / "appeal_packet.json").exists()
    assert (output_dir / "appeal_letter.md").exists()


class _FailingGenerator:
    class config:  # noqa: N801
        provider = "openai"
        model = "openai:gpt-5-mini"

    def generate(self, **kwargs):
        raise ModelCResponseError("Model returned empty content.")


def test_pipeline_falls_back_to_template_on_model_c_response_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pipeline = AppealPipeline(
        config=AppealPipelineConfig(generation_runtime="aisuite"),
        retrieval_overrides={
            "persist_directory": str(tmp_path / "chroma"),
            "collection_name": "pipeline_fallback_collection",
            "embedding_provider": "hash",
        },
    )
    monkeypatch.setattr(pipeline, "_select_generator", lambda: _FailingGenerator())

    packet = pipeline.run(
        denial_text="Payer: Aetna\nDenial Reason: Not medically necessary.\nCPT: 72148",
        chart_notes="Persistent symptoms after conservative treatment.",
        top_k=2,
    )

    assert packet.generated_output["provider"] == "template"
    assert packet.generated_output["fallback_reason"] == "Model returned empty content."
    assert packet.generated_output["fallback_from"]["provider"] == "openai"
