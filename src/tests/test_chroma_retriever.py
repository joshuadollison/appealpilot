from __future__ import annotations

from pathlib import Path

import pytest

from smallbizpulse.retrieval.chroma_retriever import (
    ChromaRetriever,
    HashEmbeddingFunction,
    RetrievalConfig,
    build_retrieval_config,
)


pytest.importorskip("chromadb")


def test_hash_embedding_is_deterministic() -> None:
    embedder = HashEmbeddingFunction(dimensions=128)
    text = "medical necessity denial for lumbar MRI"
    first = embedder([text])[0]
    second = embedder([text])[0]

    assert first == second
    assert len(first) == 128
    assert sum(abs(value) for value in first) > 0


def test_build_retrieval_config_overrides(tmp_path: Path) -> None:
    settings = tmp_path / "settings.yaml"
    settings.write_text(
        """
retrieval:
  vector_store: chroma
  persist_directory: data/interim/chroma
  collection_name: base_collection
  embedding_model: openai:text-embedding-3-small
  embedding_provider: hash
  top_k: 5
""".strip()
    )

    config = build_retrieval_config(
        settings_path=settings,
        overrides={"collection_name": "override_collection", "top_k": 3},
    )

    assert config.collection_name == "override_collection"
    assert config.top_k == 3
    assert config.embedding_provider == "hash"


def test_chroma_retriever_upsert_and_query(tmp_path: Path) -> None:
    config = RetrievalConfig(
        persist_directory=str(tmp_path / "chroma"),
        collection_name="test_collection",
        embedding_provider="hash",
        top_k=2,
    )

    retriever = ChromaRetriever(config=config)
    retriever.reset_collection()
    inserted = retriever.upsert_documents(
        [
            {
                "doc_id": "case-1",
                "text": "Diagnosis lumbar radiculopathy. Requested MRI denied for medical necessity.",
                "metadata": {"payer": "Alpha", "denial_category": "medical_necessity"},
            },
            {
                "doc_id": "case-2",
                "text": "Insurer denied due to insufficient documentation for physical therapy.",
                "metadata": {
                    "payer": "Beta",
                    "denial_category": "insufficient_documentation",
                },
            },
        ]
    )

    assert inserted == 2
    assert retriever.count() == 2

    results = retriever.query("medical necessity MRI denial", top_k=1)
    assert len(results) == 1
    assert results[0].doc_id == "case-1"

