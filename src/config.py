from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    OPENAI_API_KEY: str
    GROQ_API_KEY: str
    TAVILY_API_KEY: str
    DATABASE_URL: str = "localhost"
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    MONGODB_URI: str
    OPENAI_TEXT_MODEL: str = "gpt-4.1-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache(maxsize=1)
def get_settings():
    config = Config()  # type: ignore
    return config
