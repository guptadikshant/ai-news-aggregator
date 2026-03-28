import asyncio
import datetime

from pydantic import BaseModel, HttpUrl
from tavily import TavilyClient

from src.config import get_settings
from src.utils.content_cleaner import clean_scraped_content
from src.utils.logger import init_logging

logger = init_logging(__name__)


class SocialPostResult(BaseModel):
    """Validated container for social posts/discussions."""

    source: str
    title: str
    url: HttpUrl
    content: str

    model_config = {
        "extra": "ignore",
        "str_strip_whitespace": True,
    }


class SocialMediaScraper:
    """Async scraper for Reddit and LinkedIn using Tavily."""

    def __init__(self, *, max_results: int = 5, recency_days: int = 3) -> None:
        """Initialize the SocialMediaScraper instance.

        Args:
            max_results (int, optional): Maximum number of results to fetch. Defaults to 5.
            recency_days (int, optional): Number of days to look back for recent posts. Defaults to 3.

        Raises:
            ValueError: If required API keys are missing.
        """
        settings = get_settings()
        tavily_key = settings.TAVILY_API_KEY.get_secret_value()
        if not tavily_key:
            raise ValueError(
                "TAVILY_API_KEY is missing; set it in the environment or .env file."
            )

        self._tavily = TavilyClient(api_key=tavily_key)
        self._max_results = max_results
        self._recency_days = recency_days

        logger.info(
            f"Initialized SocialMediaScraper (max_results={max_results}, days={recency_days})."
        )

    async def _search_reddit(self, topic: str) -> list[SocialPostResult]:
        """Use Tavily to find Reddit posts/discussions on a topic.
        Args:
            topic (str): The topic to search for on Reddit.

        Returns:
            list[SocialPostResult]: A list of validated social post results from Reddit.
        """

        query = f"site:reddit.com {topic}"
        logger.info(f"Searching Reddit via Tavily for: {query}")

        try:
            response = await asyncio.to_thread(
                self._tavily.search,
                query=query,
                search_depth="advanced",
                max_results=self._max_results,
                days=self._recency_days,
                include_raw_content="markdown",
                chunks_per_source=3,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"Tavily Reddit search failed: {exc}")
            return []

        results = []
        for item in response.get("results", []):
            try:
                raw_content = item.get("raw_content")
                content = (
                    raw_content
                    if isinstance(raw_content, str) and raw_content.strip()
                    else item.get("content", "")
                )
                # Clean the content to remove markdown/HTML artifacts before validation.
                content = clean_scraped_content(content)
                results.append(
                    SocialPostResult(
                        source="Reddit",
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        content=content,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Skipping Reddit item due to validation error: {exc}")

        logger.info(f"Reddit search returned {len(results)} items.")
        return results

    async def _search_linkedin(self, topic: str) -> list[SocialPostResult]:
        """Use Tavily to find public LinkedIn posts/articles on a topic.

        Args:
            topic (str): The topic to search for on LinkedIn.

        Returns:
            list[SocialPostResult]: A list of validated social post results from LinkedIn.
        """

        query = f"site:linkedin.com/posts {topic}"
        logger.info(f"Searching LinkedIn via Tavily for: {query}")

        try:
            response = await asyncio.to_thread(
                self._tavily.search,
                query=query,
                search_depth="advanced",
                max_results=self._max_results,
                days=self._recency_days,
                include_raw_content="markdown",
                chunks_per_source=3,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"Tavily LinkedIn search failed: {exc}")
            return []

        results = []
        for item in response.get("results", []):
            try:
                raw_content = item.get("raw_content")
                content = (
                    raw_content
                    if isinstance(raw_content, str) and raw_content.strip()
                    else item.get("content", "")
                )
                # Clean the content to remove markdown/HTML artifacts before validation.
                content = clean_scraped_content(content)
                results.append(
                    SocialPostResult(
                        source="LinkedIn",
                        title=item.get("title", "No Title"),
                        url=item.get("url", ""),
                        content=content,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Skipping LinkedIn item due to validation error: {exc}")

        logger.info(f"LinkedIn search returned {len(results)} items.")
        return results

    async def fetch_social_pulse(self, topic: str) -> list[SocialPostResult]:
        """Fetch combined Reddit + LinkedIn signals for a topic.

        Args:
            topic (str): The topic to search for on social media.

        Returns:
            list[SocialPostResult]: A combined list of social post results from Reddit and LinkedIn.
        """

        reddit_task = asyncio.create_task(self._search_reddit(topic))
        linkedin_task = asyncio.create_task(self._search_linkedin(topic))

        reddit_results, linkedin_results = await asyncio.gather(
            reddit_task, linkedin_task
        )
        combined = reddit_results + linkedin_results

        logger.info(f"Collected {len(combined)} total social items.")
        return combined

    @staticmethod
    def _current_year() -> int:
        # Use UTC to avoid timezone surprises for filtering queries.
        return datetime.datetime.now(datetime.timezone.utc).year
