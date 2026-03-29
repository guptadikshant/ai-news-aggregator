from functools import lru_cache

from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer

from src.config import get_settings
from src.utils.file_reader import read_yaml

file_config = read_yaml("src/config.yaml")

text_model, embedding_model = (
    file_config["genai"]["models"]["openai"]["text"],
    file_config["genai"]["models"]["openai"]["embedding"],
)


@lru_cache(maxsize=1)
async def get_openai_client() -> ChatOpenAI:
    """Get or create openai client in singleton manner.
    This is created once for all the subsequent processes

    Returns:
        ChatOpenAI: async openai client object
    """
    return ChatOpenAI(model=text_model, temperature=0)


# @lru_cache(maxsize=1)
# async def get_groq_client() -> ChatGroq:
#     """Get or create groq client in singleton manner
#     This is created once for all the subsequent processes
#     Returns:
#         ChatGroq: async groq client object
#     """
#     return ChatGroq(model=text_model, temperature=0)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Get the embedding model and cached it for subsequent calls

    Returns:
        SentenceTransformer: loaded embedding model object
    """
    return SentenceTransformer(model_name_or_path=get_settings().EMBEDDING_MODEL)
