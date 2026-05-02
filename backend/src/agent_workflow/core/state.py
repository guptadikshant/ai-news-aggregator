from typing import Annotated

from langgraph.graph import add_messages
from pydantic import BaseModel, Field


class NewsAggregatorState(BaseModel):
    analyse_output: str | None = None
    messages: Annotated[list, add_messages]
    selected_platforms: list[str] = Field(default_factory=list)
    validated_platforms: list[str] = Field(default_factory=list)
    platforms_to_retry: list[str] = Field(default_factory=list)
    scraped_results: dict[str, list] = Field(default_factory=dict)
    retry: bool = False
    retry_count: int = 0
    max_retry: int = 2
    improved_queries: list[str] = Field(default_factory=list)
    current_step: str | None = "analyser"
    next_step: str | None = None
    final_response: str | None = None
    cache_hit: bool = False
    cache_score: float = 0.0
