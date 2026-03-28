import asyncio

from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)
from youtubesearchpython import VideosSearch

from src.utils.logger import init_logging

logger = init_logging(__name__)


class YouTubeScrapper:
    """Async wrapper for searching YouTube and fetching transcripts."""

    def __init__(
        self, max_results: int = 5, languages: list[str] | None = None
    ) -> None:
        """Intialize the YouTubeScrapper instance.

        Args:
            max_results (int, optional): Maximum number of search results to return. Defaults to 5.
            languages (list[str] | None): List of language codes for transcripts. Defaults to None.
        Returns:
            None
        """
        self.max_results = max_results
        self.languages = languages or ["en"]

    async def search_video_ids(self, query: str) -> list[str]:
        """Search YouTube for a query and return a list of video IDs."""

        return await asyncio.to_thread(self._search_video_ids_sync, query)

    def _search_video_ids_sync(self, query: str) -> list[str]:
        """Search the videos against the input query and get the video ids

        Args:
            query (str): input search query

        Returns:
            list[str]: list of video IDs
        """
        try:
            search = VideosSearch(query, limit=self.max_results)
            result = search.result()
        except TypeError as exc:  # library can break if channel id missing
            logger.warning("YouTube search parse failed for '%s': %s", query, exc)
            return []

        items = result.get("result", []) if isinstance(result, dict) else []
        return [item.get("id") for item in items if item.get("id")]

    async def fetch_transcript(self, video_id: str) -> str | None:
        """Fetch a transcript for a single video ID; returns None if unavailable."""

        return await asyncio.to_thread(self._fetch_transcript_sync, video_id)

    def _fetch_transcript_sync(self, video_id: str) -> str | None:
        """Fetched the video transcript against a video id

        Args:
            video_id (str): input video ID

        Returns:
            str | None: transcript text if available, else None
        """
        try:
            ytt_api = YouTubeTranscriptApi()
            fetched_transcript = ytt_api.fetch(video_id)
        except (
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        ) as exc:
            logger.warning(f"Transcript unavailable for video {video_id}: {exc}")
            return None

        # FetchedTranscript has a .snippets attribute with FetchedTranscriptSnippet objects
        snippets = getattr(fetched_transcript, "snippets", [])
        segments = [snippet.text.strip() for snippet in snippets if snippet.text]
        joined = " ".join(segments)
        return joined or None

    async def transcripts_for_query(self, query: str) -> list[str]:
        """Search videos for the given query and return transcripts (best-effort).

        Returns a list of transcript strings; videos without transcripts are skipped.

        Args:
            query (str): input search query

        Returns:
            list[str]: list of transcript strings
        """

        video_ids = await self.search_video_ids(query)
        transcripts = await asyncio.gather(
            *(self.fetch_transcript(video_id) for video_id in video_ids)
        )
        return [transcript for transcript in transcripts if transcript]

    @classmethod
    async def get_transcripts_for_query(
        cls,
        query: str,
        max_results: int = 5,
        languages: list[str] | None = None,
    ) -> list[str]:
        """Convenience helper to get transcripts for a query without manual instantiation.

        Args:
            query (str): input search query
            max_results (int, optional): maximum number of video results to consider. Defaults to 5.
            languages (list[str] | None): list of language codes for transcripts. Defaults to None.
        Returns:
            list[str]: list of transcript strings
        """
        try:
            scrapper = cls(max_results=max_results, languages=languages)
            transcripts = await scrapper.transcripts_for_query(query)
            logger.info(f"Fetched {len(transcripts)} transcripts for query '{query}'")
            return transcripts
        except Exception as exc:
            logger.error(f"Error fetching transcripts for query '{query}': {exc}")
            return []
