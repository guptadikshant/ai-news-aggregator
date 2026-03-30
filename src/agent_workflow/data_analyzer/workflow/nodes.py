from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.agent_workflow.prompts.data_analysis import SYSTEM_PROMPT
from src.utils.llm_client import get_openai_client
from src.utils.logger import init_logging

logger = init_logging(__name__)


class DataAnalyseModel(BaseModel):
    rejected_reason: str = Field(
        ..., description="Reason for rejecting the content item, if applicable."
    )
    rejected_platforms: Literal["youtube", "social_media", "blog_posts"] = Field(
        ...,
        description="Platform name for which content will be rejected, if applicable.",
    )


async def model_completion(system_prompt: str, user_prompt: str):
    final_response = None
    try:
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        llm = await get_openai_client()
        structured_model = llm.with_structured_output(DataAnalyseModel)
        response = await structured_model.ainvoke(prompt.format_messages())
        logger.info("Model completion successful")
        if isinstance(response, DataAnalyseModel):
            final_response = response
        else:
            final_response = DataAnalyseModel.model_validate(response)
        logger.info(f"Rejected Platform: {final_response.rejected_platforms}")
        logger.info(f"Reject Reason: {final_response.rejected_reason}")
        return final_response
    except Exception as e:
        logger.error(f"Error in model completion: {e}")
        return final_response


async def analyse_input_node(user_input: str, input_data: dict):
    final_result = []
    user_prompt = """
    Analayse the below data and let me know if the below extracted data is according to the user input.
    User input: {user_input}
    Data to analyse:
    Platform: {platform}
    Data: {value}
    """
    for platform, items in input_data.get("scraped_results", []):
        for _, item in enumerate(items, start=1):
            if isinstance(item, dict):
                for field, value in item.items():
                    if field == "content":
                        user_prompt = user_prompt.format(
                            user_input=user_input, platform=platform, value=value
                        )
                        result = await model_completion(
                            system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt
                        )
                        final_result.append(result)
            else:
                user_prompt = user_prompt.format(
                    user_input=user_input, platform=platform, value=item
                )
                result = await model_completion(
                    system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt
                )
                final_result.append(result)
    return final_result
