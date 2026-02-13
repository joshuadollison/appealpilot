from __future__ import annotations

from pathlib import Path

from smallbizpulse.workflow import run_pipeline_once


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
