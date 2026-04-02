from typing import Annotated, Literal, TypedDict

from langgraph.graph import add_messages


class NewsAggregatorState(TypedDict):
    user_input: str
    analyse_output: str
    platforms: Literal["youtube", "social_media", "blog_posts"]
    messages: Annotated[list, add_messages]
    selected_platforms: list[str]
    scraped_results: dict[str, list]
