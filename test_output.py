import asyncio

from dotenv import find_dotenv, load_dotenv

from src.agent_workflow.input_analyzer.workflow.graph import build_graph

load_dotenv(find_dotenv(), override=True)


async def main():
    graph = await build_graph()
    result = await graph.ainvoke(
        {
            "user_input": "I need a step by step tutorial how to resolve the click issue in my mouse"
        }
    )

    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
