from abc import ABC, abstractmethod
from typing import Any, Sequence
from uuid import uuid4

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)
from sentence_transformers import SentenceTransformer

from src.config import get_settings
from src.utils.logger import init_logging

logger = init_logging(__name__)

settings = get_settings()

# ── Embedding Models ─────────────────────────────────────────────────────────


class BaseEmbeddingModel(ABC):
    """Abstract base class for embedding models."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def get_dimension(self) -> int: ...


class OpenAIEmbeddingModel(BaseEmbeddingModel):
    """Embedding model backed by the OpenAI API."""

    _DIMENSION_MAP = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        settings = get_settings()
        self.model_name = model_name or settings.OPENAI_EMBEDDING_MODEL
        self._client = OpenAI(
            api_key=api_key or settings.OPENAI_API_KEY.get_secret_value()
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(input=texts, model=self.model_name)
        return [item.embedding for item in response.data]

    def get_dimension(self) -> int:
        if self.model_name in self._DIMENSION_MAP:
            return self._DIMENSION_MAP[self.model_name]
        # Fallback: embed a dummy text to figure out the dimension
        return len(self.embed(["dimension probe"])[0])


class SentenceTransformerEmbeddingModel(BaseEmbeddingModel):
    """Embedding model backed by a local SentenceTransformer model."""

    def __init__(self, model_name: str | None = None):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = SentenceTransformer(self.model_name, trust_remote_code=True)

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        dim = self._model.get_sentence_embedding_dimension()
        if dim is None:
            raise RuntimeError(
                f"Cannot determine dimension for model '{self.model_name}'"
            )
        return dim


def get_embedding_model(
    provider: str = "openai", model_name: str | None = None
) -> BaseEmbeddingModel:
    """Factory function to get an embedding model by provider name.

    Args:
        provider: "openai" or "sentence_transformer".
        model_name: Optional override for the model name.
    """
    providers = {
        "openai": OpenAIEmbeddingModel,
        "sentence_transformer": SentenceTransformerEmbeddingModel,
    }
    if provider not in providers:
        raise ValueError(
            f"Unknown provider '{provider}'. Choose from: {list(providers.keys())}"
        )
    if provider == "openai":
        logger.info(f"Using OpenAI embedding model: {model_name}")
    else:
        logger.info(f"Using SentenceTransformer embedding model: {model_name}")
    return providers[provider](model_name=model_name)


# ── Qdrant Vector Store ──────────────────────────────────────────────────────


class QdrantVectorStore:
    """High-level wrapper around the Qdrant vector database.

    Usage:
        from src.database.vector_db import QdrantVectorStore, get_embedding_model

        embedder = get_embedding_model("openai")
        store = QdrantVectorStore(embedding_model=embedder)

        store.create_collection("articles")
        store.insert("articles", texts=["hello world"], metadatas=[{"source": "web"}])
        results = store.search("articles", query="hello", limit=5)
    """

    def __init__(
        self,
        embedding_model: BaseEmbeddingModel,
        url: str | None = None,
        api_key: str | None = None,
    ):

        qdrant_url = url or settings.QDRANT_HOST_URL
        qdrant_api_key = api_key or settings.QDRANT_API_KEY.get_secret_value()

        connect_kwargs: dict[str, Any] = {}
        if qdrant_url:
            connect_kwargs["url"] = qdrant_url
        if qdrant_api_key:
            connect_kwargs["api_key"] = qdrant_api_key

        # If no URL is provided, fall back to an in-memory client (useful for tests).
        if not qdrant_url:
            connect_kwargs["location"] = ":memory:"

        self._client = QdrantClient(**connect_kwargs)
        self._embedder = embedding_model
        logger.info("Initialized QdrantVectorStore")

    # ── Collection management ────────────────────────────────────────────

    def create_collection(
        self,
        collection_name: str,
        distance: Distance = Distance.COSINE,
        on_disk: bool = False,
    ) -> None:
        """Create a new Qdrant collection. Skips if it already exists."""
        if self._client.collection_exists(collection_name):
            logger.warning(
                f"Collection '{collection_name}' already exists. Skipping creation."
            )
            return
        self._client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=self._embedder.get_dimension(),
                distance=distance,
                on_disk=on_disk,
            ),
        )
        logger.info(
            f"Created collection '{collection_name}' with distance '{distance}'"
        )

    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection and all its data."""
        self._client.delete_collection(collection_name)
        logger.info(f"Deleted collection '{collection_name}'")

    def list_collections(self) -> list[str]:
        """Return names of all collections."""
        return [c.name for c in self._client.get_collections().collections]

    # ── Insert ───────────────────────────────────────────────────────────

    def insert(
        self,
        collection_name: str,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """Embed and insert texts into a collection.

        Returns the list of point IDs that were inserted.
        """
        vectors = self._embedder.embed(texts)
        point_ids = ids or [str(uuid4()) for _ in texts]
        payloads = metadatas or [{} for _ in texts]

        # Attach the original text in the payload for convenience.
        for payload, text in zip(payloads, texts):
            payload.setdefault("text", text)

        points = [
            PointStruct(id=pid, vector=vec, payload=pl)
            for pid, vec, pl in zip(point_ids, vectors, payloads)
        ]
        self._client.upsert(collection_name=collection_name, points=points)
        logger.info(
            f"Inserted {len(points)} points into collection '{collection_name}'"
        )
        return point_ids

    def bulk_insert(
        self,
        collection_name: str,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
        batch_size: int = 64,
    ) -> list[str]:
        """Insert texts in batches to handle large datasets efficiently."""
        all_ids: list[str] = []
        for start in range(0, len(texts), batch_size):
            end = start + batch_size
            batch_texts = texts[start:end]
            batch_meta = metadatas[start:end] if metadatas else None
            batch_ids = ids[start:end] if ids else None
            inserted = self.insert(collection_name, batch_texts, batch_meta, batch_ids)
            all_ids.extend(inserted)
        logger.info(
            f"Inserted a total of {len(all_ids)} points into collection '{collection_name}'"
        )
        return all_ids

    # ── Update ───────────────────────────────────────────────────────────

    def update(
        self,
        collection_name: str,
        point_id: str,
        text: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update the vector and/or payload of an existing point."""
        if text is not None:
            vector = self._embedder.embed([text])[0]
            payload = metadata or {}
            payload.setdefault("text", text)
            self._client.upsert(
                collection_name=collection_name,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)],
            )
        elif metadata is not None:
            self._client.set_payload(
                collection_name=collection_name,
                payload=metadata,
                points=[point_id],
            )
        logger.info(f"Updated point '{point_id}' in collection '{collection_name}'")

    # ── Delete ───────────────────────────────────────────────────────────

    def delete(self, collection_name: str, point_ids: Sequence[str]) -> None:
        """Delete points by their IDs."""
        self._client.delete(
            collection_name=collection_name,
            points_selector=PointIdsList(points=list(point_ids)),
        )
        logger.info(f"Deleted points '{point_ids}' from collection '{collection_name}'")

    def delete_by_metadata(self, collection_name: str, key: str, value: Any) -> None:
        """Delete all points matching a metadata filter."""
        self._client.delete(
            collection_name=collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key=key, match=MatchValue(value=value))]
                )
            ),
        )
        logger.info(
            f"Deleted points with metadata '{key}={value}' from collection '{collection_name}'"
        )

    # ── Search ───────────────────────────────────────────────────────────

    def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 5,
        score_threshold: float | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search. Returns a list of dicts with id, score, and payload."""
        query_vector = self._embedder.embed([query])[0]

        qdrant_filter = None
        if metadata_filter:
            conditions: list[FieldCondition] = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in metadata_filter.items()
            ]
            qdrant_filter = Filter(must=conditions)  # type: ignore[arg-type]

        results = self._client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=qdrant_filter,
        )
        logger.info(
            f"Search in collection '{collection_name}' with query '{query}' returned {len(results.points)} results"
        )
        return [
            {"id": hit.id, "score": hit.score, "payload": hit.payload}
            for hit in results.points
        ]

    # ── Retrieve ─────────────────────────────────────────────────────────

    def get(self, collection_name: str, point_ids: list[str]) -> list[dict[str, Any]]:
        """Retrieve points by their IDs (no vector search)."""
        records = self._client.retrieve(
            collection_name=collection_name, ids=point_ids, with_payload=True
        )
        logger.info(
            f"Retrieved points '{point_ids}' from collection '{collection_name}'"
        )
        return [{"id": r.id, "payload": r.payload} for r in records]
