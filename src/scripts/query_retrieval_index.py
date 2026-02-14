#!/usr/bin/env python3
"""Query the Chroma retrieval index from CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from appealpilot.config.key_loader import load_local_keys
from appealpilot.retrieval import ChromaRetriever, build_retrieval_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--where-json")
    parser.add_argument("--settings-path", type=Path)
    parser.add_argument("--embedding-provider", choices=["openai", "hash", "sbert", "local"])
    parser.add_argument("--collection-name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_local_keys()

    overrides = {}
    if args.embedding_provider:
        overrides["embedding_provider"] = args.embedding_provider
    if args.collection_name:
        overrides["collection_name"] = args.collection_name

    config = build_retrieval_config(
        settings_path=args.settings_path
        or Path("src/appealpilot/config/settings.yaml"),
        overrides=overrides or None,
    )
    retriever = ChromaRetriever(config=config)

    where = json.loads(args.where_json) if args.where_json else None
    results = retriever.query(query_text=args.query, top_k=args.top_k, where=where)

    payload = {
        "collection_name": config.collection_name,
        "embedding_provider": retriever.embedding_provider,
        "result_count": len(results),
        "results": [
            {
                "doc_id": item.doc_id,
                "distance": item.distance,
                "metadata": dict(item.metadata),
                "text": item.text,
            }
            for item in results
        ],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
