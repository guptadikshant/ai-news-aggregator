from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.agent_workflow.input_analyzer.workflow.state import InputAnalyser
from src.agent_workflow.prompts.input_analysis import SYSTEM_PROMPT
from src.utils.llm_client import get_openai_client
from src.utils.logger import init_logging

logger = init_logging(__name__)


class PlatformRequired(BaseModel):
    analysis: str
    platform_needed: list[Literal["youtube", "social_media", "blog_posts"]] = Field(
        ..., description="The values with which the the information can be extracted"
    )


async def model_completion(
    system_prompt: str, user_prompt: str
) -> PlatformRequired | None:
    try:
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        llm = await get_openai_client()
        structured_llm = llm.with_structured_output(PlatformRequired)
        response = await structured_llm.ainvoke(prompt.format_messages())
        logger.info("Model completion successful")
        return response # type: ignore
    except Exception as e:
        logger.error(f"Error in model completion: {e}")
        return None


async def analyse_input(state: InputAnalyser) -> dict:
    try:
        user_input = state["user_input"]
        if not user_input:
            return {"analyse_output": "", "platforms": None}

        model_response = await model_completion(
            system_prompt=SYSTEM_PROMPT, user_prompt=user_input
        )

        if not model_response:
            return {"analyse_output": "", "platforms": None}
        logger.info("Successfully analysed the input")
        return {
            "analyse_output": model_response.analysis,
            "platforms": model_response.platform_needed,
        }
    except Exception as e:
        logger.error(f"Error in analysing input: {e}")
        return {"analyse_output": "", "platforms": None}