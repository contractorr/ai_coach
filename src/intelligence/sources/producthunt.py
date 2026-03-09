"""Product Hunt RSS scraper."""

from datetime import datetime
from time import mktime

import feedparser
import httpx
import structlog
from bs4 import BeautifulSoup

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from intelligence.utils import detect_tags
from retry_utils import http_retry
from shared_types import IntelSource

logger = structlog.get_logger().bind(source="producthunt")

PH_FEED_URL = "https://www.producthunt.com/feed"


class ProductHuntScraper(BaseScraper):
    """Scrape Product Hunt RSS feed for new product launches."""

    def __init__(self, storage: IntelStorage, feed_url: str = PH_FEED_URL, max_items: int = 20):
        super().__init__(storage)
        self.feed_url = feed_url
        self.max_items = max_items

    @property
    def source_name(self) -> str:
        return IntelSource.PRODUCTHUNT

    @http_retry(exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.RequestError))
    async def scrape(self) -> list[IntelItem]:
        try:
            response = await self.client.get(self.feed_url)
            response.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning("producthunt.fetch_failed", error=str(e))
            return []

        feed = feedparser.parse(response.text)
        items = []

        for entry in feed.entries[: self.max_items]:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime.fromtimestamp(mktime(entry.published_parsed))

            summary = ""
            if hasattr(entry, "summary"):
                summary = BeautifulSoup(entry.summary, "html.parser").get_text()[:500]

            title = entry.get("title", "Untitled")
            tags = detect_tags(title)
            tags = list(dict.fromkeys(["product-launch"] + tags))[:5]

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

        logger.info("producthunt.scraped", count=len(items))
        return items
