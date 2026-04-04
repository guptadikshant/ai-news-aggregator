import asyncio

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from src.agent_workflow.core.models import PlatformRequired
from src.agent_workflow.core.state import NewsAggregatorState
from src.agent_workflow.core.tools import TOOL_REGISTRY
from src.agent_workflow.prompts.input_analysis import SYSTEM_PROMPT
from src.utils.llm_client import get_openai_client
from src.utils.logger import init_logging

logger = init_logging(__name__)


async def model_completion(system_prompt: str, user_prompt: str) -> dict | None:
    """
    Generate a model completion based on the provided system and user prompts.
    Args:
        system_prompt (str): The system prompt to guide the model's behavior.
        user_prompt (str): The user prompt containing the query or input.

    Returns:
        dict | None: The model's response as a dictionary, or None if an error occurs.
    """
    try:
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        llm = get_openai_client()
        structured_llm = llm.with_structured_output(PlatformRequired)
        response = await structured_llm.ainvoke(prompt.format_messages())
        logger.info("Model completion successful")
        if isinstance(response, PlatformRequired):
            platform_result = response
        else:
            platform_result = PlatformRequired.model_validate(response)

        logger.info(f"Platform selected: {platform_result.platform_needed}")
        logger.info(f"Analysis: {platform_result.analysis}")
        return platform_result.model_dump()
    except Exception as e:
        logger.error(f"Error in model completion: {e}")
        return None


async def analyse_input_node(state: NewsAggregatorState) -> dict:
    """
    Analyse the user's input and determine the required platforms.

    Args:
        state (NewsAggregatorState): The current state of the news aggregator.

    Returns:
        dict: A dictionary containing the analysis output and selected platforms.
    """
    try:
        user_query = state["messages"][-1].content
        if not user_query:
            return {"analyse_output": "", "selected_platforms": None}

        model_response = await model_completion(
            system_prompt=SYSTEM_PROMPT, user_prompt=user_query
        )

        if not model_response:
            return {"analyse_output": "", "selected_platforms": None}
        logger.info("Successfully analysed the input")
        return {
            "analyse_output": model_response["analysis"],
            "selected_platforms": model_response["platform_needed"],
        }
    except Exception as e:
        logger.error(f"Error in analysing input: {e}")
        return {"analyse_output": "", "selected_platforms": None}


async def call_tools_node(state: NewsAggregatorState) -> dict:
    """
    Call the appropriate tools based on the selected platforms and user query.
    Args:
        state (NewsAggregatorState): The current state of the news aggregator.

    Returns:
        dict: A dictionary containing the results from the called tools.
    """
    user_query = state.messages[-1].content
    if state.platforms_to_retry:
        platforms = state.platforms_to_retry
        logger.info(f"[call_tools] Retrying platforms: {platforms}")
    else:
        platforms = state.selected_platforms
        logger.info(f"[call_tools] Using selected platforms: {platforms}")

    async def _call_scraper(platform: str) -> tuple[str, list]:
        entry = TOOL_REGISTRY.get(platform)
        if not entry:
            logger.warning(f"[call_tools] Skipping unknown platform: {platform}")
            return platform, []
        logger.info(f"[call_tools] Calling scraper for: {platform}")
        result = await entry["fn"](**{entry["param"]: user_query})
        return platform, result

    results = await asyncio.gather(*[_call_scraper(p) for p in platforms])
    scraped = {platform: data for platform, data in results}

    logger.info(f"[call_tools] Finished scraping: {list(scraped.keys())}")
    return {"scraped_results": scraped}
