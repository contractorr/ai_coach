"""Y Combinator jobs scraper — hiring signals from HN /jobs."""

import asyncio
from datetime import datetime
from typing import Optional

import httpx
import structlog
from bs4 import BeautifulSoup

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from intelligence.utils import detect_tags
from retry_utils import http_retry
from shared_types import IntelSource

logger = structlog.get_logger().bind(source="yc_jobs")

HN_API = "https://hacker-news.firebaseio.com/v0"


class YCJobsScraper(BaseScraper):
    """Scrape YC/HN job stories for hiring signals."""

    def __init__(self, storage: IntelStorage, max_items: int = 30, concurrency: int = 10):
        super().__init__(storage)
        self.max_items = max_items
        self.concurrency = concurrency

    @property
    def source_name(self) -> str:
        return IntelSource.YC_JOBS

    @http_retry(exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.RequestError))
    async def scrape(self) -> list[IntelItem]:
        try:
            response = await self.client.get(f"{HN_API}/jobstories.json")
            response.raise_for_status()
            job_ids = response.json()[: self.max_items]
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning("yc_jobs.fetch_failed", error=str(e))
            return []

        semaphore = asyncio.Semaphore(self.concurrency)
        tasks = [self._fetch_job(semaphore, jid) for jid in job_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        items = [r for r in results if isinstance(r, IntelItem)]
        logger.info("yc_jobs.scraped", count=len(items))
        return items

    async def _fetch_job(self, semaphore: asyncio.Semaphore, job_id: int) -> Optional[IntelItem]:
        async with semaphore:
            try:
                response = await self.client.get(f"{HN_API}/item/{job_id}.json")
                response.raise_for_status()
                data = response.json()
                if not data:
                    return None

                title = data.get("title", "")
                text = ""
                if data.get("text"):
                    text = BeautifulSoup(data["text"], "html.parser").get_text()[:500]

                url = data.get("url", f"https://news.ycombinator.com/item?id={job_id}")

                tags = detect_tags(title)
                tags = list(dict.fromkeys(["hiring", "yc"] + tags))[:5]

                return IntelItem(
                    source=self.source_name,
                    title=title,
                    url=url,
                    summary=text or title,
                    published=datetime.fromtimestamp(data["time"]) if data.get("time") else None,
                    tags=tags,
                )
            except (httpx.RequestError, KeyError, TypeError) as e:
                logger.debug("yc_jobs.item_failed", job_id=job_id, error=str(e))
                return None
