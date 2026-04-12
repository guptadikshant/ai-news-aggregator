from langchain_core.messages import HumanMessage, SystemMessage

from ...utils.llm_client import get_openai_client
from ...utils.logger import init_logging
from ..core.models import FormatResponseOutput
from ..core.state import NewsAggregatorState
from ..prompts.format_response import SYSTEM_PROMPT

logger = init_logging(__name__)


async def model_completion(system_prompt: str, user_prompt: str):
    """
    Generate a model completion based on the provided system and user prompts.
    Args:
        system_prompt (str): The system prompt to guide the model's behavior.
        user_prompt (str): The user prompt containing the query or input.

    Returns:
        dict | None: The model's response as a dictionary, or None if an error occurs.
    """
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        llm = get_openai_client()
        structured_llm = llm.with_structured_output(FormatResponseOutput)
        response = await structured_llm.ainvoke(messages)
        logger.info("Model completion successful")
        return (
            response.model_dump()
            if isinstance(response, FormatResponseOutput)
            else None
        )
    except Exception as e:
        logger.error(f"Error in model completion: {e}")
        return None


async def output_formatter_node(state: NewsAggregatorState) -> dict:

    user_query = state.messages[-1].content
    validated_platforms = state.validated_platforms or []
    scraped_data = state.scraped_results
    content_to_format = ""

    for platform, data in scraped_data.items():
        formatted_content = []
        if platform in validated_platforms:
            if platform == "blog_posts":
                for post in data:
                    formatted_content.append(
                        f"Platform: {platform}\nTitle: {post.title} \nContent: {post.content}\n\n"
                    )
            elif platform == "social_media":
                for post in data:
                    formatted_content.append(
                        f"Platform: {platform}\nSource: {post.source} \nTitle: {post.title} \nContent: {post.content}\n\n"
                    )

            elif platform == "youtube":
                for video in data:
                    formatted_content.append(
                        f"Platform: {platform}\nTranscript: {video}\n\n"
                    )
        content_to_format += (" ").join(formatted_content)

    if not content_to_format:
        content_to_format = (" ").join(
            f"Platform: {platform}\nData: {data}\n\n"
            for platform, data in scraped_data.items()
        )

    user_prompt = (
        f"## User Query: {user_query}\n\n ## Data to format:\n{content_to_format}"
    )
    formatted_output = await model_completion(SYSTEM_PROMPT, user_prompt)

    logger.info(f"Formatted output generated for user query: {user_query}")

    final_response = (
        formatted_output.get("final_response", "")
        if isinstance(formatted_output, dict)
        else formatted_output
    )
    return {"final_response": final_response or ""}
