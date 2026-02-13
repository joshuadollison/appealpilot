"""Chroma-backed retrieval store for AppealPilot Model B."""

from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


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
    )
    config.validate()
    return config


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


def resolve_embedding_provider(config: RetrievalConfig) -> str:
    """Resolve embedding provider with sensible runtime fallback."""

    provider = config.embedding_provider.strip().lower()
    if provider not in {"openai", "hash"}:
        raise RetrievalConfigError(
            "embedding_provider must be one of: openai, hash."
        )

    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        return "hash"
    return provider


def _build_embedding_function(config: RetrievalConfig) -> tuple[Any, str]:
    provider = resolve_embedding_provider(config)
    if provider == "hash":
        return HashEmbeddingFunction(dimensions=config.hash_dimensions), provider

    try:
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
    except Exception as exc:  # pragma: no cover - import errors vary by env
        raise RetrievalConfigError(
            "OpenAI embeddings require chromadb OpenAI embedding dependencies."
        ) from exc

    return (
        OpenAIEmbeddingFunction(
            api_key=os.environ["OPENAI_API_KEY"],
            model_name=config.embedding_model.split(":", maxsplit=1)[-1],
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
            texts.append(document.text)
            metadatas.append(dict(document.metadata))

        if not ids:
            return 0

        self.collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
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
