"""Hacker News scraper."""

import asyncio
from datetime import datetime
from typing import Optional

import httpx
import structlog
from bs4 import BeautifulSoup

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from intelligence.utils import detect_hn_tags
from retry_utils import http_retry
from shared_types import IntelSource

logger = structlog.get_logger().bind(source="hackernews")


class HackerNewsScraper(BaseScraper):
    """Async scraper for Hacker News top stories."""

    API_BASE = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, storage: IntelStorage, max_stories: int = 30, concurrency: int = 10):
        super().__init__(storage)
        self.max_stories = max_stories
        self.concurrency = concurrency

    @property
    def source_name(self) -> str:
        return IntelSource.HACKERNEWS

    @http_retry(exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.RequestError))
    async def scrape(self) -> list[IntelItem]:
        """Fetch top HN stories concurrently."""
        items = []

        try:
            logger.debug("Fetching HN top stories")
            response = await self.client.get(f"{self.API_BASE}/topstories.json")
            response.raise_for_status()
            story_ids = response.json()[: self.max_stories]
            logger.debug("Got %d story IDs", len(story_ids))

            # Fetch stories concurrently with semaphore for rate limiting
            semaphore = asyncio.Semaphore(self.concurrency)
            tasks = [self._fetch_story_limited(semaphore, sid) for sid in story_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, IntelItem):
                    items.append(result)

        except httpx.RequestError as e:
            logger.error("Failed to fetch HN stories: %s", e)

        logger.info("Scraped %d HN stories", len(items))
        return items

    async def _fetch_story_limited(
        self, semaphore: asyncio.Semaphore, story_id: int
    ) -> Optional[IntelItem]:
        """Fetch story with rate limiting."""
        async with semaphore:
            return await self._fetch_story(story_id)

    async def _fetch_story(self, story_id: int) -> Optional[IntelItem]:
        """Fetch single story details."""
        try:
            response = await self.client.get(f"{self.API_BASE}/item/{story_id}.json")
            response.raise_for_status()
            data = response.json()

            if not data or data.get("type") != "story":
                return None

            summary_parts = []
            if data.get("score"):
                summary_parts.append(f"{data['score']} points")
            if data.get("descendants"):
                summary_parts.append(f"{data['descendants']} comments")
            if data.get("text"):
                text = BeautifulSoup(data["text"], "html.parser").get_text()[:300]
                summary_parts.append(text)

            return IntelItem(
                source=self.source_name,
                title=data.get("title", "Untitled"),
                url=data.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                summary=" | ".join(summary_parts) if summary_parts else "",
                published=datetime.fromtimestamp(data["time"]) if data.get("time") else None,
                tags=detect_hn_tags(data.get("title", "")),
            )

        except httpx.RequestError as e:
            logger.debug("Failed to fetch story %d: %s", story_id, e)
            return None
