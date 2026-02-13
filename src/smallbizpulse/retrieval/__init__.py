"""Retrieval components for Model B (RAG)."""

from .chroma_retriever import (
    RetrievalConfig,
    RetrievalDocument,
    RetrievedDocument,
    ChromaRetriever,
    build_retrieval_config,
    resolve_embedding_provider,
)
from .dfs_ingest import load_dfs_documents

__all__ = [
    "RetrievalConfig",
    "RetrievalDocument",
    "RetrievedDocument",
    "ChromaRetriever",
    "build_retrieval_config",
    "resolve_embedding_provider",
    "load_dfs_documents",
]
