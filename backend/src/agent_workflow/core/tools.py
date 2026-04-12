from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool

from src.scrappers.blog_posts_scrapper import BlogPostsScraper
from src.scrappers.social_media_scrapper import SocialMediaScraper
from src.scrappers.youtube_scrapper import YouTubeScrapper

youtube_scrapper = YouTubeScrapper()
blog_posts_scraper = BlogPostsScraper()
social_media_scrapper = SocialMediaScraper()

TOOL_REGISTRY: dict[str, dict] = {
    "youtube": {
        "fn": youtube_scrapper.get_transcripts_for_query,
        "param": "query",
    },
    "blog_posts": {
        "fn": blog_posts_scraper.search,
        "param": "topic",
    },
    "social_media": {
        "fn": social_media_scrapper.fetch_social_pulse,
        "param": "topic",
    },
}


@tool
async def search_youtube(query: str) -> list[dict]:
    """Search YouTube for videos and return transcripts related to the query."""
    return await youtube_scrapper.get_transcripts_for_query(query=query)  # type:ignore


@tool
async def search_blog_posts(topic: str) -> list[dict]:
    """Search blog platforms like Medium and Dev.to for articles on the topic."""
    return await blog_posts_scraper.search(topic=topic)  # type:ignore


@tool
async def search_social_media(topic: str) -> list[dict]:
    """Search social media platforms like LinkedIn and Reddit for posts on the topic."""
    return await social_media_scrapper.fetch_social_pulse(topic=topic)  # type:ignore


tools = [search_youtube, search_blog_posts, search_social_media]
openai_tools = [convert_to_openai_tool(t) for t in tools]
