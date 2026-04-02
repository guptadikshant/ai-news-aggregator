from typing import Literal

from pydantic import BaseModel, Field


class PlatformRequired(BaseModel):
    analysis: str
    platform_needed: list[Literal["youtube", "social_media", "blog_posts"]] = Field(
        ..., description="The values with which the the information can be extracted"
    )
