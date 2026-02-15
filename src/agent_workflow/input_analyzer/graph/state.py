from pydantic import BaseModel, Field


class InputAnalyzerGraphState(BaseModel):
    """State representation for the Input Analyzer Graph."""

    user_input: str = Field(..., description="The original user input to be analyzed.")
    extracted_entities: list[str] = Field(
        default_factory=list,
        description="List of entities extracted from the user input.",
    )
