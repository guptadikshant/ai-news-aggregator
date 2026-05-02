from functools import lru_cache

from src.config import get_settings
from src.database.vector_db import QdrantVectorStore, get_embedding_model
from src.utils.logger import init_logging

logger = init_logging(__name__)

settings = get_settings()


@lru_cache(maxsize=1)
def _get_vector_store() -> QdrantVectorStore:
    """Return a singleton QdrantVectorStore using OpenAI embeddings."""
    embedder = get_embedding_model(provider="openai")
    return QdrantVectorStore(embedding_model=embedder)


def initialize_cache() -> None:
    """Create the query_cache collection in Qdrant if it doesn't exist."""
    try:
        store = _get_vector_store()
        store.create_collection(settings.CACHE_COLLECTION_NAME)
        logger.info(f"Cache collection '{settings.CACHE_COLLECTION_NAME}' ready")
    except Exception as e:
        logger.warning("Failed to initialize cache (Qdrant may be unreachable): %s", e)


def search_cache(query: str) -> dict | None:
    """Search for a semantically similar query in the cache.

    Returns a dict with 'final_response' and 'score' if a match is found
    above the configured similarity threshold, otherwise None.
    """
    if not settings.CACHE_ENABLED:
        return None

    try:
        store = _get_vector_store()
        results = store.search(
            collection_name=settings.CACHE_COLLECTION_NAME,
            query=query,
            limit=1,
            score_threshold=settings.CACHE_SIMILARITY_THRESHOLD,
        )
    except Exception as e:
        logger.warning("Cache search failed: %s", e)
        return None

    if not results:
        logger.info("Cache miss for query: %s", query)
        return None

    top = results[0]
    logger.info("Cache hit for query: %s (score=%.4f)", query, top["score"])
    return {
        "final_response": top["payload"]["final_response"],
        "score": top["score"],
    }


def save_to_cache(
    query: str, final_response: str, selected_platforms: list[str]
) -> None:
    """Store a query and its response in the cache collection."""
    if not settings.CACHE_ENABLED:
        return

    try:
        store = _get_vector_store()
        store.insert(
            collection_name=settings.CACHE_COLLECTION_NAME,
            texts=[query],
            metadatas=[
                {
                    "final_response": final_response,
                    "selected_platforms": selected_platforms,
                }
            ],
        )
    except Exception as e:
        logger.warning("Failed to save to cache: %s", e)
    logger.info("Saved response to cache for query: %s", query)


# ── LangGraph node functions ────────────────────────────────────────────────


async def check_cache_node(state) -> dict:
    """LangGraph node: check if a semantically similar query exists in cache."""
    query = state.messages[-1].content
    result = search_cache(query)

    if result:
        return {
            "cache_hit": True,
            "cache_score": result["score"],
            "final_response": result["final_response"],
        }

    return {"cache_hit": False, "cache_score": 0.0}


async def save_to_cache_node(state) -> dict:
    """LangGraph node: persist the query + response to cache after a fresh run."""
    if state.cache_hit:
        return {}

    query = state.messages[-1].content
    save_to_cache(
        query=query,
        final_response=state.final_response or "",
        selected_platforms=state.selected_platforms,
    )
    return {}

def route_after_cache(state) -> str:
    """Conditional edge: skip the pipeline when a cache hit is found."""
    if state.cache_hit:
        return "end"
    return "input_analyser"
