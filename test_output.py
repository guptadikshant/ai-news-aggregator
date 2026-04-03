import asyncio

from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import HumanMessage

from src.agent_workflow.output_validator.graph import build_graph
from src.utils.logger import init_logging

logger = init_logging(__name__)

load_dotenv(find_dotenv(), override=True)

SCRAPED_DATA = {
    "youtube": [
        "Hey everybody, Cedric here with Pear Crew! Today I'm going to show you how to fix your\nmouse from double clicking or not registering clicks. This problem usually occurs with mice that\nhave been in use for a while and need their tension springs re-adjusted...",
        "hi guys if windows 11 can't click then let's fix this issue what you have to do just press ctrl shift and escape keys together from your keyboard...",
        "Is your laptop mouse or trackpad not working? It may be because of a\nrandom glitch, oil or grime, other accessories, a software\nissue or your mouse settings. Here's how to fix it...",
        "Hi guys, if you are facing the problem of cursor freezing, cursor hanging, cursor disappearing or cursor jumping, then you are at the right place...",
        "hello beautiful people i am Ramesh and i am a pc technician in this video I'm going to show you how you can fix if your mouse is not recognized or not working on your laptop or desktop...",
    ],
    "blog_posts": [
        {
            "title": "Fixing the left-click of a Evoluent VerticalMouse C (VMCR) - Medium",
            "url": "https://medium.com/@makahane42/fixing-the-left-click-of-a-evoluent-verticalmouse-c-vmcr-9382bc9c7486",
            "content": "This article will cover disassembly of the mouse in order to examine the circuits around the left-click button and how I went about fixing the left-click button...",
            "score": 0.33,
        },
        {
            "title": "If Mouse Keeps Clicking By Itself on Window 10! How to Fix it?",
            "url": "https://medium.com/@UpdatedNews/if-mouse-keeps-clicking-by-itself-on-window-10-how-to-fix-it-9af85ded76a9",
            "content": "Sometimes, users reported that mouse is clicking on its own on Window 10 when they play game or if they are working...",
            "score": 0.21,
        },
        {
            "title": "Using Cursor IDE Like a Pro: My Personal Guide to Building ...",
            "url": "https://medium.com/@vikasranjan008/using-cursor-ide-like-a-pro",
            "content": "Over the past few weeks, I've been diving deep into Cursor IDE, exploring how it can go from just another code assistant to a real productivity booster...",
            "score": 0.09,
        },
        {
            "title": "How I Code These Days - Patryk Kabaj - Substack",
            "url": "https://patrykkabaj.substack.com/p/how-i-code-these-days",
            "content": "My current AI-engineering workflow multiplying my skills without sacrificing quality...",
            "score": 0.07,
        },
        {
            "title": "Click-Based Productivity in the Modern Workplace",
            "url": "https://medium.com/@louisretief1/click-based-productivity-in-the-modern-workplace",
            "content": "This conversation examined the concept of click-based productivity in modern office environments...",
            "score": 0.06,
        },
    ],
}


async def main():
    user_input = (
        "I need a step by step tutorial how to resolve the click issue in my mouse"
    )
    logger.info(f"User Input: {user_input}")

    graph = build_graph()
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "analyse_output": "User wants a step-by-step tutorial to fix mouse click issues. Selected youtube and blog_posts as relevant platforms.",
            "platforms": "youtube",
            "selected_platforms": ["youtube", "blog_posts"],
            "scraped_results": SCRAPED_DATA,  # type: ignore
        }
    )

    print("=" * 60)
    print(f"Retry: {result['retry']}")
    print(f"Retry Count: {result['retry_count']}")
    print(f"Selected Platforms: {result['selected_platforms']}")
    print(f"Current Step: {result['current_step']}")
    print(f"Final Response: {result['final_response']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
