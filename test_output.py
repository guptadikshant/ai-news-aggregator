import asyncio

from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import HumanMessage

from src.agent_workflow.agent_pipeline import create_agent_pipeline
from src.utils.logger import init_logging

logger = init_logging(__name__)

load_dotenv(find_dotenv(), override=True)


async def main():
    user_input = "Latest AI news about new models release in 2026?"
    logger.info(f"User Input: {user_input}")

    pipeline = create_agent_pipeline()
    result = await pipeline.ainvoke(
        {
            "messages": [HumanMessage(content=user_input)]  # type: ignore
        }
    )

    print("=" * 60)
    print(f"Retry: {result['retry']}")
    print(f"Retry Count: {result['retry_count']}")
    print(f"Selected Platforms: {result['selected_platforms']}")
    print(f"Platforms to Retry: {result['platforms_to_retry']}")
    print(f"Current Step: {result['current_step']}")
    print(f"Next Step: {result['next_step']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
