"""Shared index build utilities for CLI and dashboard usage."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .chroma_retriever import ChromaRetriever, build_retrieval_config
from .dfs_ingest import load_dfs_documents

DEFAULT_DFS_XLSX = Path("data/raw/dfs_external_appeals/ny_dfs_external_appeals_all_years.xlsx")


def rebuild_retrieval_index(
    xlsx_path: Path = DEFAULT_DFS_XLSX,
    limit: int | None = None,
    reset: bool = True,
    settings_path: Path | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build or refresh the retrieval collection and return build stats."""

    config = build_retrieval_config(
        settings_path=settings_path or Path("src/smallbizpulse/config/settings.yaml"),
        overrides=overrides or None,
    )

    if reset:
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
    documents = load_dfs_documents(xlsx_path=xlsx_path, limit=limit)
    inserted = retriever.upsert_documents(documents)

    return {
        "embedding_provider": retriever.embedding_provider,
        "collection_name": config.collection_name,
        "documents_upserted": inserted,
        "collection_size": retriever.count(),
        "persist_directory": config.persist_directory,
        "xlsx_path": str(xlsx_path),
    }
