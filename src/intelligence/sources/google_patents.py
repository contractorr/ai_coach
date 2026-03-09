"""Google Patents RSS scraper — tech patent filings by category."""

from datetime import datetime
from time import mktime
from typing import Optional

import feedparser
import httpx
import structlog
from bs4 import BeautifulSoup

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from intelligence.utils import detect_tags
from retry_utils import http_retry
from shared_types import IntelSource

logger = structlog.get_logger().bind(source="google_patents")

# Default RSS feeds for tech patent categories
DEFAULT_FEEDS = [
    "https://patents.google.com/api/feed?q=CPC%3DG06N&num=20",  # AI/ML
    "https://patents.google.com/api/feed?q=CPC%3DH04L&num=20",  # Networking
]


class GooglePatentsScraper(BaseScraper):
    """Scrape Google Patents RSS feeds for tech patent filings."""

    def __init__(
        self,
        storage: IntelStorage,
        feeds: Optional[list[str]] = None,
        max_per_feed: int = 15,
    ):
        super().__init__(storage)
        self.feeds = feeds or DEFAULT_FEEDS
        self.max_per_feed = max_per_feed

    @property
    def source_name(self) -> str:
        return IntelSource.GOOGLE_PATENTS

    @http_retry(exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.RequestError))
    async def scrape(self) -> list[IntelItem]:
        all_items: list[IntelItem] = []

        for feed_url in self.feeds:
            items = await self._scrape_feed(feed_url)
            all_items.extend(items)

        logger.info("google_patents.scraped", count=len(all_items), feeds=len(self.feeds))
        return all_items

    async def _scrape_feed(self, feed_url: str) -> list[IntelItem]:
        try:
            response = await self.client.get(feed_url)
            response.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning("google_patents.feed_failed", url=feed_url, error=str(e))
            return []

        feed = feedparser.parse(response.text)
        items = []

        for entry in feed.entries[: self.max_per_feed]:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime.fromtimestamp(mktime(entry.published_parsed))

            summary = ""
            if hasattr(entry, "summary"):
                summary = BeautifulSoup(entry.summary, "html.parser").get_text()[:500]

            title = entry.get("title", "Untitled Patent")
            tags = detect_tags(title)
            tags = list(dict.fromkeys(["patent"] + tags))[:5]

            items.append(
                IntelItem(
                    source=self.source_name,
                    title=title,
                    url=entry.get("link", ""),
                    summary=summary,
                    published=published,
                    tags=tags,
                )
            )

        return items
