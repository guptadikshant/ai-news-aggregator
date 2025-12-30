import datetime

import httpx
from pydantic import BaseModel, HttpUrl
from tavily import TavilyClient

from src.config import get_settings
from src.utils.logger import init_logging

logger = init_logging()


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
    """Synchronous scraper for Reddit and LinkedIn using Tavily and Serper."""

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

        serper_key = settings.SERPER_API_KEY.get_secret_value()
        if not serper_key:
            logger.warning(
                "SERPER_API_KEY is missing; LinkedIn scraping will fail without it."
            )

        self._tavily = TavilyClient(api_key=tavily_key)
        self._serper_key = serper_key
        self._max_results = max_results
        self._recency_days = recency_days

        logger.info(
            f"Initialized SocialMediaScraper (max_results={max_results}, days={recency_days})."
        )

    def _search_reddit(self, topic: str) -> list[SocialPostResult]:
        """Use Tavily to find Reddit posts/discussions on a topic.
        Args:
            topic (str): The topic to search for on Reddit.

        Returns:
            list[SocialPostResult]: A list of validated social post results from Reddit.
        """

        query = f"site:reddit.com {topic}"
        logger.info(f"Searching Reddit via Tavily for: {query}")

        try:
            response = self._tavily.search(
                query=query,
                search_depth="advanced",
                max_results=self._max_results,
                days=self._recency_days,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"Tavily Reddit search failed: {exc}")
            return []

        results = []
        for item in response.get("results", []):
            try:
                results.append(
                    SocialPostResult(
                        source="Reddit",
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        content=item.get("content", ""),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Skipping Reddit item due to validation error: {exc}")

        logger.info(f"Reddit search returned {len(results)} items.")
        return results

    def _search_linkedin(self, topic: str) -> list[SocialPostResult]:
        """Use Serper (Google) to find public LinkedIn posts/snippets.

        Args:
            topic (str): The topic to search for on LinkedIn.

        Returns:
            list[SocialPostResult]: A list of validated social post results from LinkedIn.
        """

        if not self._serper_key:
            logger.error("SERPER_API_KEY not configured; skipping LinkedIn search.")
            return []

        query = f'site:linkedin.com/posts {topic} "{self._current_year()}"'
        payload = {
            "q": query,
            "num": self._max_results,
            "tbs": "qdr:w",  # Past week
        }
        headers = {
            "X-API-KEY": self._serper_key,
            "Content-Type": "application/json",
        }

        logger.info(f"Searching LinkedIn via Serper for: {query}")

        try:
            with httpx.Client(timeout=20) as client:
                resp = client.post(
                    "https://google.serper.dev/search", headers=headers, json=payload
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.exception(f"Serper LinkedIn search failed: {exc}")
            return []

        results = []
        for item in data.get("organic", []):
            try:
                results.append(
                    SocialPostResult(
                        source="LinkedIn",
                        title=item.get("title", "No Title"),
                        url=item.get("link", ""),
                        content=item.get("snippet", ""),
                    )
                )
            except Exception as exc:
                logger.warning(f"Skipping LinkedIn item due to validation error: {exc}")

        logger.info(f"LinkedIn search returned {len(results)} items.")
        return results

    def fetch_social_pulse(self, topic: str) -> list[SocialPostResult]:
        """Fetch combined Reddit + LinkedIn signals for a topic.

        Args:
            topic (str): The topic to search for on social media.

        Returns:
            list[SocialPostResult]: A combined list of social post results from Reddit and LinkedIn.
        """

        reddit_results = self._search_reddit(topic)
        linkedin_results = self._search_linkedin(topic)
        combined = reddit_results + linkedin_results

        logger.info(f"Collected {len(combined)} total social items.")
        return combined

    @staticmethod
    def _current_year() -> int:
        # Use UTC to avoid timezone surprises for filtering queries.
        return datetime.datetime.now(datetime.timezone.utc).year
