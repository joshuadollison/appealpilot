from __future__ import annotations

from appealpilot.retrieval.chroma_retriever import (
    CHARS_PER_TOKEN_ESTIMATE,
    ChromaRetriever,
    DEFAULT_INSURANCE_BERT_MODEL,
    RetrievalConfig,
    _resolve_embedding_model_name,
    resolve_embedding_provider,
)


def _build_stub_retriever(
    *,
    provider: str,
    openai_max_batch_tokens: int = 200_000,
    openai_max_input_tokens: int = 8_000,
    upsert_batch_size: int = 128,
) -> ChromaRetriever:
    retriever = ChromaRetriever.__new__(ChromaRetriever)
    retriever.embedding_provider = provider
    retriever.config = RetrievalConfig(
        embedding_provider=provider,
        openai_max_batch_tokens=openai_max_batch_tokens,
        openai_max_input_tokens=openai_max_input_tokens,
        upsert_batch_size=upsert_batch_size,
    )
    return retriever


def test_local_alias_maps_to_sbert() -> None:
    config = RetrievalConfig(embedding_provider="local")
    assert resolve_embedding_provider(config) == "sbert"


def test_insurance_alias_maps_to_insurance_bert() -> None:
    config = RetrievalConfig(embedding_provider="insurance")
    assert resolve_embedding_provider(config) == "insurance_bert"


def test_openai_without_key_falls_back_to_hash(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = RetrievalConfig(embedding_provider="openai")
    assert resolve_embedding_provider(config) == "hash"


def test_insurance_provider_uses_insurance_default_over_sbert_prefixed_model() -> None:
    resolved = _resolve_embedding_model_name(
        raw_model="sbert:sentence-transformers/all-MiniLM-L6-v2",
        expected_providers=["insurance_bert"],
        default_model=DEFAULT_INSURANCE_BERT_MODEL,
    )
    assert resolved == DEFAULT_INSURANCE_BERT_MODEL


def test_openai_text_is_truncated_before_embedding_request() -> None:
    retriever = _build_stub_retriever(
        provider="openai",
        openai_max_input_tokens=5,
    )
    long_text = "x" * 100
    normalized = retriever._normalize_text_for_upsert(long_text)
    assert len(normalized) == 5 * CHARS_PER_TOKEN_ESTIMATE


def test_openai_batches_respect_token_budget() -> None:
    retriever = _build_stub_retriever(
        provider="openai",
        openai_max_batch_tokens=20,
        openai_max_input_tokens=20,
        upsert_batch_size=10,
    )
    ids = ["a", "b", "c"]
    texts = ["x" * 30, "y" * 30, "z" * 30]  # each ~10 tokens with estimate.
    metadatas = [{}, {}, {}]

    batches = list(retriever._iter_upsert_batches(ids, texts, metadatas))
    assert len(batches) == 2
    assert batches[0][0] == ["a", "b"]
    assert batches[1][0] == ["c"]
