from typing import Literal

from pydantic import BaseModel, Field


class PlatformRequired(BaseModel):
    analysis: str
    platform_needed: list[Literal["youtube", "social_media", "blog_posts"]] = Field(
        ..., description="The values with which the the information can be extracted"
    )
    confidence_score: float = Field(
        ..., description="how much confident you are when suggesting this platforms"
    )


class ValidateOutput(BaseModel):
    is_valid: bool = Field(
        default=True,
        description="If the data is valid or not as per the query",
    )
    feedback: str = Field(
        ..., description="Feedback which describes why data is not according to user"
    )
    retry: bool = Field(
        default=False,
        description="Whether to retry the tool calls or not, if False then the final response will be generated with the current data",
    )
