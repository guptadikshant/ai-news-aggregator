import json
from typing import Literal

from pydantic import BaseModel, Field

from src.agent_workflow.input_analyzer.workflow.state import InputAnalyser
from src.agent_workflow.prompts.input_analysis import SYSTEM_PROMPT
from src.utils.llm_client import get_groq_client


class PlatformRequired(BaseModel):
    analysis: str
    platform_needed: list[
        Literal["youtube", "social_media", "blog_posts", "news_articles"]
    ] = Field(
        ..., description="The values with which the the information can be extracted"
    )


async def model_completion(system_prompt: str, user_prompt: str) -> str | None:
    groq_client = await get_groq_client()
    chat_completion = await groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        temperature=0,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "PlatformRequired",
                "schema": PlatformRequired.model_json_schema(),
            },
        },
    )

    return chat_completion.choices[0].message.content


async def analyse_input(state: InputAnalyser) -> dict:
    user_input = state["user_input"]
    if not user_input:
        return {"analyse_output": "", "platforms": None}

    model_response = await model_completion(
        system_prompt=SYSTEM_PROMPT, user_prompt=user_input
    )

    if not model_response:
        return {"analyse_output": "", "platforms": None}

    json_resp = json.loads(model_response)  # type: ignore

    if json_resp:
        return {
            "analyse_output": json_resp["analysis"],
            "platforms": json_resp["platform_needed"],
        }
    else:
        return {}