#!/usr/bin/env python3
"""Run full denial-to-appeal workflow and export packet artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from smallbizpulse.workflow import run_pipeline_once


def _read_text_arg(path: Path | None, inline_text: str | None) -> str:
    if inline_text:
        return inline_text
    if path and path.exists():
        return path.read_text()
    raise ValueError("Provide either inline text or a valid file path.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--denial-text")
    parser.add_argument("--denial-text-file", type=Path)
    parser.add_argument("--chart-notes")
    parser.add_argument("--chart-notes-file", type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--generation-runtime", choices=["auto", "aisuite", "template"], default="auto")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--collection-name")
    parser.add_argument("--embedding-provider", choices=["openai", "hash"])
    args = parser.parse_args()

    denial_text = _read_text_arg(args.denial_text_file, args.denial_text)
    chart_notes = ""
    if args.chart_notes or args.chart_notes_file:
        chart_notes = _read_text_arg(args.chart_notes_file, args.chart_notes)

    retrieval_overrides = {}
    if args.collection_name:
        retrieval_overrides["collection_name"] = args.collection_name
    if args.embedding_provider:
        retrieval_overrides["embedding_provider"] = args.embedding_provider

    packet, export_dir = run_pipeline_once(
        denial_text=denial_text,
        chart_notes=chart_notes,
        top_k=args.top_k,
        generation_runtime=args.generation_runtime,
        output_dir=args.output_dir,
        retrieval_overrides=retrieval_overrides or None,
    )

    print(f"Exported packet to: {export_dir}")
    print(f"Category: {packet.classification.category} ({packet.classification.confidence:.2f})")
    print(f"Evidence hits: {len(packet.evidence_items)}")
    print(f"Generator provider: {packet.generated_output.get('provider')}")


if __name__ == "__main__":
    main()
