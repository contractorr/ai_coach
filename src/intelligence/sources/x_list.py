"""X/Twitter List scraper via API v2."""

from __future__ import annotations

from datetime import datetime

import httpx
import structlog

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from retry_utils import http_retry
from shared_types import IntelSource

logger = structlog.get_logger().bind(source="x_list")

API_BASE = "https://api.twitter.com/2"


class XListScraper(BaseScraper):
    """Fetch tweets from an X/Twitter List using API v2."""

    def __init__(
        self,
        storage: IntelStorage,
        bearer_token: str | None = None,
        list_id: str | None = None,
        max_tweets: int = 100,
    ):
        super().__init__(storage)
        self.bearer_token = bearer_token
        self.list_id = list_id
        self.max_tweets = min(max_tweets, 100)  # API max per request

    @property
    def source_name(self) -> str:
        return IntelSource.X_LIST

    @http_retry(exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.RequestError))
    async def scrape(self) -> list[IntelItem]:
        """Fetch tweets from the configured X List."""
        if not self.bearer_token or not self.list_id:
            logger.warning("x_list.missing_config", has_token=bool(self.bearer_token))
            return []

        items: list[IntelItem] = []

        try:
            self._client_headers["Authorization"] = f"Bearer {self.bearer_token}"

            response = await self.client.get(
                f"{API_BASE}/lists/{self.list_id}/tweets",
                params={
                    "tweet.fields": "text,created_at,author_id,public_metrics",
                    "expansions": "author_id",
                    "user.fields": "username",
                    "max_results": str(self.max_tweets),
                },
            )
            response.raise_for_status()
            data = response.json()

            tweets = data.get("data", [])
            if not tweets:
                logger.info("x_list.no_tweets", list_id=self.list_id)
                return []

            # Build author_id → username lookup from expansions
            authors: dict[str, str] = {}
            for user in data.get("includes", {}).get("users", []):
                authors[user["id"]] = user.get("username", "unknown")

            for tweet in tweets:
                text = tweet.get("text", "").strip()
                if not text:
                    continue

                tweet_id = tweet["id"]
                author_id = tweet.get("author_id", "")
                username = authors.get(author_id, "unknown")
                created_at = None
                if tweet.get("created_at"):
                    try:
                        created_at = datetime.fromisoformat(
                            tweet["created_at"].replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        pass

                items.append(
                    IntelItem(
                        source=self.source_name,
                        title=f"{username}: {text[:80]}",
                        url=f"https://x.com/{username}/status/{tweet_id}",
                        summary=text,
                        published=created_at,
                        tags=[username],
                    )
                )

        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                logger.warning("x_list.auth_failed", status=e.response.status_code)
                return []
            if e.response.status_code == 404:
                logger.warning("x_list.list_not_found", list_id=self.list_id)
                return []
            raise
        except httpx.RequestError as e:
            logger.error("x_list.request_failed", error=str(e))

        logger.info("x_list.scraped", count=len(items), list_id=self.list_id)
        return items
