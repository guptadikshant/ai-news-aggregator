import asyncio

from dotenv import find_dotenv, load_dotenv

from src.agent_workflow.input_analyzer.workflow.graph import build_graph
from src.utils.logger import init_logging

logger = init_logging(__name__)

load_dotenv(find_dotenv(), override=True)


async def main():
    user_input = "I need a step by step tutorial how to resolve the click issue in my mouse"
    logger.info(f"User Input: {user_input}")
    graph = await build_graph()
    result = await graph.ainvoke(
        {
            "user_input": user_input
        }
    )

    logger.info(f"Analysis Result: {result['analyse_output']}")
    logger.info(f"Platforms Needed: {result['platforms']}")


if __name__ == "__main__":
    asyncio.run(main())
