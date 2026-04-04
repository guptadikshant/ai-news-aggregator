from typing import Annotated

from langgraph.graph import add_messages
from pydantic import BaseModel


class NewsAggregatorState(BaseModel):
    messages: Annotated[list, add_messages]
    selected_platforms: list[str]
    platforms_to_retry: list[str] = []
    scraped_results: dict[str, list]
    retry: bool = False
    retry_count: int = 0
    max_retry: int = 2
    current_step: str | None = "analyser"
    next_step: str | None = None
    final_response: str | None = None
