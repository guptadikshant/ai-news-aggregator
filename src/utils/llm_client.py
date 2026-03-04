from functools import lru_cache

from groq import AsyncGroq
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from src.config import get_settings


@lru_cache(maxsize=1)
async def get_openai_client() -> AsyncOpenAI:
    """Get or create openai client in singleton manner.
    This is created once for all the subsequent processes

    Returns:
        AsyncOpenAI: async openai client object
    """
    return AsyncOpenAI(api_key=get_settings().OPENAI_API_KEY.get_secret_value())


@lru_cache(maxsize=1)
async def get_groq_client() -> AsyncGroq:
    """Get or create groq client in singleton manner
    This is created once for all the subsequent processes
    Returns:
        AsyncGroq: async groq client object
    """
    return AsyncGroq(api_key=get_settings().GROQ_API_KEY.get_secret_value())


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Get the embedding model and cached it for subsequent calls

    Returns:
        SentenceTransformer: loaded embedding model object
    """
    return SentenceTransformer(model_name_or_path=get_settings().EMBEDDING_MODEL)
