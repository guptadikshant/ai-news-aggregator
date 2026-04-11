from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Configuration class to hold all the settings for the application."""

    OPENAI_API_KEY: SecretStr = SecretStr("")
    GROQ_API_KEY: SecretStr = SecretStr("")
    TAVILY_API_KEY: SecretStr = SecretStr("")
    SERPER_API_KEY: SecretStr = SecretStr("")
    DATABASE_URL: str = "localhost"
    DATABASE_USER: SecretStr = SecretStr("")
    DATABASE_PASSWORD: SecretStr = SecretStr("")
    MONGODB_URI: SecretStr = SecretStr("")
    OPENAI_TEXT_MODEL: str = "gpt-4.1-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    TEXT_MODEL: str = "qwen/qwen3-32b"
    EMBEDDING_MODEL: str = "Qwen/Qwen3-Embedding-0.6B"
    QDRANT_HOST_URL: str = ""
    QDRANT_API_KEY: SecretStr = SecretStr("")
    LANGFUSE_SECRET_KEY: SecretStr = SecretStr("")
    LANGFUSE_PUBLIC_KEY: SecretStr = SecretStr("")
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"
    CACHE_COLLECTION_NAME: str = "query_cache"
    CACHE_SIMILARITY_THRESHOLD: float = 0.90
    CACHE_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache(maxsize=1)
def get_settings():
    """Get the configuration settings in singleton manner."""
    config = Config()
    return config
