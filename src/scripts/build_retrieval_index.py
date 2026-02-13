#!/usr/bin/env python3
"""Build the Chroma retrieval index from DFS external appeals XLSX."""

from __future__ import annotations

import argparse
from pathlib import Path

from smallbizpulse.config.key_loader import load_local_keys
from smallbizpulse.retrieval import rebuild_retrieval_index

DEFAULT_DFS_XLSX = Path(
    "data/raw/dfs_external_appeals/ny_dfs_external_appeals_all_years.xlsx"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsx-path", type=Path, default=DEFAULT_DFS_XLSX)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--settings-path", type=Path)
    parser.add_argument("--embedding-provider", choices=["openai", "hash"])
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

    result = rebuild_retrieval_index(
        xlsx_path=args.xlsx_path,
        limit=args.limit,
        reset=args.reset,
        settings_path=args.settings_path
        or Path("src/smallbizpulse/config/settings.yaml"),
        overrides=overrides,
    )
    print(f"Embedding provider: {result['embedding_provider']}")
    print(f"Collection: {result['collection_name']}")
    print(f"Documents upserted: {result['documents_upserted']}")
    print(f"Collection size: {result['collection_size']}")


if __name__ == "__main__":
    main()
