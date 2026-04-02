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
    """Node 2: Call only the scrapers for the selected platforms in parallel."""
    user_query = state["messages"][-1].content
    platforms = state["selected_platforms"]

    async def _call_scraper(platform: str) -> tuple[str, list]:
        entry = TOOL_REGISTRY.get(platform)
        if not entry:
            print(f"[call_tools] Skipping unknown platform: {platform}")
            return platform, []
        print(f"[call_tools] Calling scraper for: {platform}")
        result = await entry["fn"](**{entry["param"]: user_query})
        return platform, result

    results = await asyncio.gather(*[_call_scraper(p) for p in platforms])
    scraped = {platform: data for platform, data in results}

    print(f"[call_tools] Finished scraping: {list(scraped.keys())}")
    return {"scraped_results": scraped}
