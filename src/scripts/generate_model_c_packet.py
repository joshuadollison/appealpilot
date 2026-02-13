#!/usr/bin/env python3
"""Generate a Model C appeal packet with aisuite.

Example:
  PYTHONPATH=src python src/scripts/generate_model_c_packet.py \
    --case-json /tmp/case.json \
    --evidence-json /tmp/evidence.json \
    --model groq:llama-3.3-70b-versatile \
    --output /tmp/appeal_packet.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from smallbizpulse.models import ModelCGenerator, build_model_c_config


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-json", type=Path, required=True)
    parser.add_argument("--evidence-json", type=Path, required=True)
    parser.add_argument("--attachments-json", type=Path)
    parser.add_argument("--settings-path", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    overrides: dict[str, Any] = {}
    if args.model:
        overrides["model"] = args.model
    if args.temperature is not None:
        overrides["temperature"] = args.temperature
    if args.max_tokens is not None:
        overrides["max_tokens"] = args.max_tokens

    config = build_model_c_config(
        settings_path=args.settings_path or Path("src/smallbizpulse/config/settings.yaml"),
        overrides=overrides or None,
    )
    generator = ModelCGenerator(config=config)

    case_summary = _read_json(args.case_json)
    evidence = _read_json(args.evidence_json)
    attachments = _read_json(args.attachments_json) if args.attachments_json else []

    result = generator.generate(
        case_summary=case_summary,
        retrieved_evidence=evidence,
        required_attachments=attachments,
    )

    rendered = json.dumps(result, indent=2, ensure_ascii=True)
    if args.output:
        args.output.write_text(rendered + "\n")
        print(f"Wrote Model C response to {args.output}")
        return

    print(rendered)


if __name__ == "__main__":
    main()
