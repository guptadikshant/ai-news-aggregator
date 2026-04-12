from typing import Annotated

from langgraph.graph import add_messages
from pydantic import BaseModel


class NewsAggregatorState(BaseModel):
    analyse_output: str | None = None
    messages: Annotated[list, add_messages]
    selected_platforms: list[str] = []
    validated_platforms: list[str] = []
    platforms_to_retry: list[str] = []
    scraped_results: dict[str, list] = {}
    retry: bool = False
    retry_count: int = 0
    max_retry: int = 2
    improved_queries: list[str] = []
    current_step: str | None = "analyser"
    next_step: str | None = None
    final_response: str | None = None
    cache_hit: bool = False
    cache_score: float = 0.0
