#!/usr/bin/env python3
"""Build the Chroma retrieval index from DFS external appeals XLSX."""

from __future__ import annotations

import argparse
from pathlib import Path

from smallbizpulse.retrieval import (
    ChromaRetriever,
    build_retrieval_config,
    load_dfs_documents,
)

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

    overrides = {}
    if args.embedding_provider:
        overrides["embedding_provider"] = args.embedding_provider
    if args.collection_name:
        overrides["collection_name"] = args.collection_name

    config = build_retrieval_config(
        settings_path=args.settings_path
        or Path("src/smallbizpulse/config/settings.yaml"),
        overrides=overrides or None,
    )

    if args.reset:
        try:
            import chromadb
        except ImportError:
            chromadb = None

        if chromadb is not None:
            client = chromadb.PersistentClient(path=config.persist_directory)
            try:
                client.delete_collection(config.collection_name)
            except Exception:
                pass

    retriever = ChromaRetriever(config=config)

    documents = load_dfs_documents(xlsx_path=args.xlsx_path, limit=args.limit)
    inserted = retriever.upsert_documents(documents)

    print(f"Embedding provider: {retriever.embedding_provider}")
    print(f"Collection: {config.collection_name}")
    print(f"Documents upserted: {inserted}")
    print(f"Collection size: {retriever.count()}")


if __name__ == "__main__":
    main()
