"""Chroma-backed retrieval store for AppealPilot Model B."""

from __future__ import annotations

import hashlib
import logging
import math
import os
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Iterable, Mapping, Sequence

DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")
CHARS_PER_TOKEN_ESTIMATE = 3
DEFAULT_OPENAI_MAX_BATCH_TOKENS = 200_000
DEFAULT_OPENAI_MAX_INPUT_TOKENS = 8_000
DEFAULT_UPSERT_BATCH_SIZE = 128
DEFAULT_SBERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_INSURANCE_BERT_MODEL = "llmware/industry-bert-insurance-v0.1"
_SBERT_MODEL_CACHE: dict[str, Any] = {}
_SBERT_MODEL_CACHE_LOCK = Lock()


class RetrievalConfigError(ValueError):
    """Raised when retrieval configuration is invalid."""


@dataclass(frozen=True)
class RetrievalConfig:
    """Runtime config for Chroma-based retrieval."""

    vector_store: str = "chroma"
    persist_directory: str = "data/interim/chroma"
    collection_name: str = "dfs_appeals_cases"
    embedding_model: str = "openai:text-embedding-3-small"
    embedding_provider: str = "openai"
    top_k: int = 5
    hash_dimensions: int = 256
    openai_max_batch_tokens: int = DEFAULT_OPENAI_MAX_BATCH_TOKENS
    openai_max_input_tokens: int = DEFAULT_OPENAI_MAX_INPUT_TOKENS
    upsert_batch_size: int = DEFAULT_UPSERT_BATCH_SIZE

    def validate(self) -> None:
        if self.vector_store != "chroma":
            raise RetrievalConfigError("Only `chroma` vector store is supported in v1.")
        if not self.persist_directory:
            raise RetrievalConfigError("persist_directory is required.")
        if not self.collection_name:
            raise RetrievalConfigError("collection_name is required.")
        if self.top_k < 1:
            raise RetrievalConfigError("top_k must be >= 1.")
        if self.hash_dimensions < 32:
            raise RetrievalConfigError("hash_dimensions must be >= 32.")
        if self.openai_max_batch_tokens < 1:
            raise RetrievalConfigError("openai_max_batch_tokens must be >= 1.")
        if self.openai_max_input_tokens < 1:
            raise RetrievalConfigError("openai_max_input_tokens must be >= 1.")
        if self.upsert_batch_size < 1:
            raise RetrievalConfigError("upsert_batch_size must be >= 1.")
        if self.openai_max_batch_tokens < self.openai_max_input_tokens:
            raise RetrievalConfigError(
                "openai_max_batch_tokens must be >= openai_max_input_tokens."
            )


@dataclass(frozen=True)
class RetrievalDocument:
    """Document payload inserted into the vector store."""

    doc_id: str
    text: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedDocument:
    """Single retrieval result returned by query."""

    doc_id: str
    text: str
    metadata: Mapping[str, Any]
    distance: float | None


def _to_int(value: Any, fallback: int) -> int:
    if value is None or value == "":
        return fallback
    return int(value)


def _load_retrieval_from_settings(settings_path: Path) -> dict[str, Any]:
    if not settings_path.exists():
        return {}

    try:
        import yaml
    except ImportError as exc:
        raise RetrievalConfigError(
            "PyYAML is required to read settings.yaml. Install with `pip install PyYAML`."
        ) from exc

    loaded = yaml.safe_load(settings_path.read_text()) or {}
    if not isinstance(loaded, dict):
        return {}

    retrieval = loaded.get("retrieval", {})
    if retrieval is None:
        return {}
    if not isinstance(retrieval, dict):
        raise RetrievalConfigError("`retrieval` in settings.yaml must be a mapping.")
    return retrieval


def build_retrieval_config(
    settings_path: Path = DEFAULT_SETTINGS_PATH,
    overrides: Mapping[str, Any] | None = None,
) -> RetrievalConfig:
    """Build retrieval config from settings, env vars, and explicit overrides."""

    base = _load_retrieval_from_settings(settings_path)
    if overrides:
        base = {**base, **dict(overrides)}

    config = RetrievalConfig(
        vector_store=os.getenv("RETRIEVAL_VECTOR_STORE", base.get("vector_store", "chroma")),
        persist_directory=os.getenv(
            "RETRIEVAL_PERSIST_DIRECTORY", base.get("persist_directory", "data/interim/chroma")
        ),
        collection_name=os.getenv(
            "RETRIEVAL_COLLECTION_NAME", base.get("collection_name", "dfs_appeals_cases")
        ),
        embedding_model=os.getenv(
            "RETRIEVAL_EMBEDDING_MODEL",
            base.get("embedding_model", "openai:text-embedding-3-small"),
        ),
        embedding_provider=os.getenv(
            "RETRIEVAL_EMBEDDING_PROVIDER",
            base.get("embedding_provider", "openai"),
        ),
        top_k=_to_int(os.getenv("RETRIEVAL_TOP_K", base.get("top_k")), 5),
        hash_dimensions=_to_int(
            os.getenv("RETRIEVAL_HASH_DIMENSIONS", base.get("hash_dimensions")), 256
        ),
        openai_max_batch_tokens=_to_int(
            os.getenv(
                "RETRIEVAL_OPENAI_MAX_BATCH_TOKENS",
                base.get("openai_max_batch_tokens"),
            ),
            DEFAULT_OPENAI_MAX_BATCH_TOKENS,
        ),
        openai_max_input_tokens=_to_int(
            os.getenv(
                "RETRIEVAL_OPENAI_MAX_INPUT_TOKENS",
                base.get("openai_max_input_tokens"),
            ),
            DEFAULT_OPENAI_MAX_INPUT_TOKENS,
        ),
        upsert_batch_size=_to_int(
            os.getenv("RETRIEVAL_UPSERT_BATCH_SIZE", base.get("upsert_batch_size")),
            DEFAULT_UPSERT_BATCH_SIZE,
        ),
    )
    config.validate()
    return config


def _normalize_embedding_provider(provider: str) -> str:
    normalized = provider.strip().lower().replace("-", "_")
    aliases = {
        "openai": "openai",
        "hash": "hash",
        "sbert": "sbert",
        "sentence_transformers": "sbert",
        "local": "sbert",
        "insurance_bert": "insurance_bert",
        "industry_bert_insurance": "insurance_bert",
        "insurance": "insurance_bert",
    }
    return aliases.get(normalized, normalized)


def _resolve_embedding_model_name(
    raw_model: str,
    expected_providers: str | Sequence[str],
    default_model: str,
) -> str:
    providers: set[str]
    if isinstance(expected_providers, str):
        providers = {_normalize_embedding_provider(expected_providers)}
    else:
        providers = {_normalize_embedding_provider(item) for item in expected_providers}

    model = (raw_model or "").strip()
    if not model:
        return default_model

    if ":" not in model:
        return model

    provider_prefix, model_name = model.split(":", maxsplit=1)
    if _normalize_embedding_provider(provider_prefix) in providers:
        candidate = model_name.strip()
        if candidate:
            return candidate
    return default_model


class HashEmbeddingFunction:
    """Deterministic local embedding function for offline/demo usage."""

    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    @staticmethod
    def name() -> str:
        return "hash_embedding_v1"

    @classmethod
    def build_from_config(cls, config: Mapping[str, Any] | None) -> "HashEmbeddingFunction":
        dimensions = 256
        if isinstance(config, Mapping):
            raw_dimensions = config.get("dimensions")
            if raw_dimensions is not None and str(raw_dimensions).strip():
                dimensions = int(raw_dimensions)
        return cls(dimensions=dimensions)

    def is_legacy(self) -> bool:
        return False

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    def get_config(self) -> dict[str, Any]:
        return {"type": "hash", "dimensions": self.dimensions}

    def __call__(self, input: Sequence[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def embed_documents(self, input: Sequence[str]) -> list[list[float]]:
        return self(input)

    def embed_query(self, input: str | Sequence[str]) -> list[list[float]]:
        if isinstance(input, str):
            return [self._embed(input)]
        return self(input)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = TOKEN_PATTERN.findall((text or "").lower())
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimensions
            weight = (int.from_bytes(digest[4:8], "little") % 1000) / 1000.0 + 0.5
            sign = -1.0 if (digest[8] & 1) else 1.0
            vector[index] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class SentenceTransformerEmbeddingFunction:
    """Local semantic embeddings via sentence-transformers."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = self._load_model(model_name)

    @staticmethod
    def _load_model(model_name: str) -> Any:
        cached = _SBERT_MODEL_CACHE.get(model_name)
        if cached is not None:
            return cached

        with _SBERT_MODEL_CACHE_LOCK:
            cached = _SBERT_MODEL_CACHE.get(model_name)
            if cached is not None:
                return cached

            try:
                from sentence_transformers import SentenceTransformer
                from transformers.utils import logging as transformers_logging
            except ImportError as exc:
                raise RetrievalConfigError(
                    "sentence-transformers is required for local embeddings. "
                    "Install with `pip install sentence-transformers`."
                ) from exc

            os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
            logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
            logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
            logging.getLogger("transformers").setLevel(logging.ERROR)
            transformers_logging.set_verbosity_error()
            warnings.filterwarnings(
                "ignore",
                message="You are sending unauthenticated requests to the HF Hub.*",
            )

            model = SentenceTransformer(model_name)
            _SBERT_MODEL_CACHE[model_name] = model
            return model

    @staticmethod
    def name() -> str:
        return "sentence_transformers_embedding_v1"

    def is_legacy(self) -> bool:
        return False

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    def get_config(self) -> dict[str, Any]:
        return {"type": "sentence_transformers", "model_name": self.model_name}

    def __call__(self, input: Sequence[str]) -> list[list[float]]:
        if not input:
            return []
        vectors = self._model.encode(
            list(input),
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return vectors.tolist()

    def embed_documents(self, input: Sequence[str]) -> list[list[float]]:
        return self(input)

    def embed_query(self, input: str | Sequence[str]) -> list[list[float]]:
        if isinstance(input, str):
            return self([input])
        return self(input)


def resolve_embedding_provider(config: RetrievalConfig) -> str:
    """Resolve embedding provider with sensible runtime fallback."""

    provider = _normalize_embedding_provider(config.embedding_provider)
    if provider not in {"openai", "hash", "sbert", "insurance_bert"}:
        raise RetrievalConfigError(
            "embedding_provider must be one of: openai, hash, sbert, insurance_bert (or local)."
        )

    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        return "hash"
    return provider


def _build_embedding_function(config: RetrievalConfig) -> tuple[Any, str]:
    provider = resolve_embedding_provider(config)
    if provider == "hash":
        return HashEmbeddingFunction(dimensions=config.hash_dimensions), provider
    if provider == "sbert":
        model_name = _resolve_embedding_model_name(
            raw_model=config.embedding_model,
            expected_providers=["sbert", "insurance_bert"],
            default_model=DEFAULT_SBERT_MODEL,
        )
        return SentenceTransformerEmbeddingFunction(model_name=model_name), provider
    if provider == "insurance_bert":
        model_name = _resolve_embedding_model_name(
            raw_model=config.embedding_model,
            expected_providers=["insurance_bert"],
            default_model=DEFAULT_INSURANCE_BERT_MODEL,
        )
        return SentenceTransformerEmbeddingFunction(model_name=model_name), provider

    try:
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
    except Exception as exc:  # pragma: no cover - import errors vary by env
        raise RetrievalConfigError(
            "OpenAI embeddings require chromadb OpenAI embedding dependencies."
        ) from exc

    return (
        OpenAIEmbeddingFunction(
            api_key=os.environ["OPENAI_API_KEY"],
            model_name=_resolve_embedding_model_name(
                raw_model=config.embedding_model,
                expected_providers="openai",
                default_model="text-embedding-3-small",
            ),
        ),
        provider,
    )


class ChromaRetriever:
    """Thin wrapper around a Chroma persistent collection."""

    def __init__(self, config: RetrievalConfig):
        config.validate()
        self.config = config

        try:
            import chromadb
        except ImportError as exc:
            raise RetrievalConfigError(
                "chromadb is required. Install with `pip install chromadb`."
            ) from exc

        Path(config.persist_directory).mkdir(parents=True, exist_ok=True)
        self._embedding_function, self.embedding_provider = _build_embedding_function(config)
        self.client = chromadb.PersistentClient(path=config.persist_directory)
        try:
            self.collection = self.client.get_or_create_collection(
                name=config.collection_name,
                embedding_function=self._embedding_function,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:
            message = str(exc).lower()
            if "embedding function" in message or "conflict" in message:
                raise RetrievalConfigError(
                    "Existing collection embedding configuration conflicts with current "
                    "embedding provider. Rebuild with reset to recreate the collection."
                ) from exc
            raise

    def reset_collection(self) -> None:
        """Delete and recreate the configured collection."""

        try:
            self.client.delete_collection(self.config.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            embedding_function=self._embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return int(self.collection.count())

    def _coerce_document(self, payload: RetrievalDocument | Mapping[str, Any]) -> RetrievalDocument:
        if isinstance(payload, RetrievalDocument):
            return payload

        if not isinstance(payload, Mapping):
            raise RetrievalConfigError("Document payload must be RetrievalDocument or mapping.")

        doc_id = str(payload.get("doc_id", "")).strip()
        text = str(payload.get("text", "")).strip()
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise RetrievalConfigError("Document metadata must be a mapping.")
        if not doc_id:
            raise RetrievalConfigError("Document doc_id is required.")
        if not text:
            raise RetrievalConfigError("Document text is required.")

        return RetrievalDocument(doc_id=doc_id, text=text, metadata=dict(metadata))

    def _estimate_tokens(self, text: str) -> int:
        cleaned = text.strip()
        if not cleaned:
            return 1
        return max(1, math.ceil(len(cleaned) / CHARS_PER_TOKEN_ESTIMATE))

    def _normalize_text_for_upsert(self, text: str) -> str:
        if self.embedding_provider != "openai":
            return text

        max_chars = self.config.openai_max_input_tokens * CHARS_PER_TOKEN_ESTIMATE
        if len(text) <= max_chars:
            return text
        return text[:max_chars]

    def _iter_upsert_batches(
        self,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> Iterable[tuple[list[str], list[str], list[dict[str, Any]]]]:
        max_batch_size = max(1, self.config.upsert_batch_size)
        if self.embedding_provider != "openai":
            for start in range(0, len(ids), max_batch_size):
                end = start + max_batch_size
                yield ids[start:end], texts[start:end], metadatas[start:end]
            return

        max_batch_tokens = max(1, self.config.openai_max_batch_tokens)
        batch_ids: list[str] = []
        batch_texts: list[str] = []
        batch_metadatas: list[dict[str, Any]] = []
        batch_tokens = 0

        for doc_id, text, metadata in zip(ids, texts, metadatas):
            estimated_tokens = self._estimate_tokens(text)
            should_flush = bool(batch_ids) and (
                len(batch_ids) >= max_batch_size
                or (batch_tokens + estimated_tokens) > max_batch_tokens
            )
            if should_flush:
                yield batch_ids, batch_texts, batch_metadatas
                batch_ids = []
                batch_texts = []
                batch_metadatas = []
                batch_tokens = 0

            batch_ids.append(doc_id)
            batch_texts.append(text)
            batch_metadatas.append(metadata)
            batch_tokens += estimated_tokens

        if batch_ids:
            yield batch_ids, batch_texts, batch_metadatas

    def upsert_documents(
        self, documents: Iterable[RetrievalDocument | Mapping[str, Any]]
    ) -> int:
        """Upsert documents into Chroma and return count upserted."""

        ids: list[str] = []
        texts: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for raw_document in documents:
            document = self._coerce_document(raw_document)
            ids.append(document.doc_id)
            texts.append(self._normalize_text_for_upsert(document.text))
            metadatas.append(dict(document.metadata))

        if not ids:
            return 0

        for batch_ids, batch_texts, batch_metadatas in self._iter_upsert_batches(
            ids=ids,
            texts=texts,
            metadatas=metadatas,
        ):
            self.collection.upsert(
                ids=batch_ids,
                documents=batch_texts,
                metadatas=batch_metadatas,
            )
        return len(ids)

    def query(
        self,
        query_text: str,
        top_k: int | None = None,
        where: Mapping[str, Any] | None = None,
    ) -> list[RetrievedDocument]:
        """Run vector search and return normalized result objects."""

        n_results = top_k or self.config.top_k
        query_result = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=dict(where) if where else None,
        )

        ids = (query_result.get("ids") or [[]])[0]
        docs = (query_result.get("documents") or [[]])[0]
        metas = (query_result.get("metadatas") or [[]])[0]
        distances = (query_result.get("distances") or [[]])[0]

        results: list[RetrievedDocument] = []
        for index, doc_id in enumerate(ids):
            text = docs[index] if index < len(docs) else ""
            metadata = metas[index] if index < len(metas) and metas[index] else {}
            distance = distances[index] if index < len(distances) else None
            results.append(
                RetrievedDocument(
                    doc_id=doc_id,
                    text=text,
                    metadata=metadata,
                    distance=distance,
                )
            )
        return results
