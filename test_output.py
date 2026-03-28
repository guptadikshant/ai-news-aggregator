import asyncio

from dotenv import find_dotenv, load_dotenv

from src.agent_workflow.input_analyzer.workflow.graph import build_graph
from src.utils.logger import init_logging
from langchain_core.messages import HumanMessage

logger = init_logging(__name__)

load_dotenv(find_dotenv(), override=True)


async def main():
    user_input = (
        "I need a step by step tutorial how to resolve the click issue in my mouse"
    )
    logger.info(f"User Input: {user_input}")
    graph = await build_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=user_input)]} # type:ignore
    )
    print(f"Selected Platforms: {result['selected_platforms']}")
    print("=" * 50)
    print(f"Scraped Platforms:  {list(result['scraped_results'].items())}")


if __name__ == "__main__":
    asyncio.run(main())
