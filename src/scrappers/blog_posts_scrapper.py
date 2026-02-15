from typing import Sequence

from pydantic import BaseModel
from tavily import TavilyClient

from src.config import get_settings
from src.utils.logger import init_logging

logger = init_logging()


class BlogPostResult(BaseModel):
    """Validated container for Tavily blog search results."""

    title: str
    url: str
    content: str
    score: float | None = None

    model_config = {
        "extra": "ignore",
        "str_strip_whitespace": True,
    }


class BlogPostsScraper:
    """Async wrapper around TavilyClient tailored for technical blog discovery."""

    def __init__(
        self,
        include_domains: Sequence[str] | None = None,
        max_results: int = 5,
    ) -> None:
        """Initialize the BlogPostsScraper instance.

        Args:
            include_domains (Sequence[str] | None, optional): Domains to include in the search. Defaults to None.
            max_results (int, optional): Maximum number of results to return. Defaults to 5.

        Raises:
            ValueError: If TAVILY_API_KEY is not set in the environment.
        """
        settings = get_settings()
        api_key = settings.TAVILY_API_KEY.get_secret_value()
        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY is missing; set it in the environment or .env file."
            )

        self._client = TavilyClient(api_key=api_key)
        self._include_domains = (
            list(include_domains)
            if include_domains
            else [
                "medium.com",
                "dev.to",
                "hashnode.com",
                "substack.com",
                "github.com",
                "stackoverflow.blog",
            ]
        )
        self._max_results = max_results

        logger.info("Initialized BlogPostsScraper with Tavily client.")

    def search(self, query: str) -> list[BlogPostResult]:
        """Search for technical blog posts on a given topic.

        Args:
            topic (str): The topic to search for.

        Returns:
            list[BlogPostResult]: A list of validated blog post results.
        """
        logger.info(f"Searching Tavily for topic: {query}")

        response = self._client.search(
            query=query,
            topic="general",
            search_depth="advanced",
            max_results=self._max_results,
            include_domains=self._include_domains,
        )

        results = []
        for item in response.get("results", []):
            results.append(
                BlogPostResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score"),
                )
            )

        logger.info(f"Tavily returned {len(results)} blog results.")
        return results
