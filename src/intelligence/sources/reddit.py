"""Reddit scraper for career and startup subreddits."""

from datetime import datetime
from typing import Optional

import httpx
import structlog

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from intelligence.utils import detect_tags
from retry_utils import http_retry
from shared_types import IntelSource

logger = structlog.get_logger().bind(source="reddit")

# Default subreddits for career/startup content
DEFAULT_SUBREDDITS = [
    "cscareerquestions",
    "startups",
    "SideProject",
    "ExperiencedDevs",
]


class RedditScraper(BaseScraper):
    """Async scraper for Reddit subreddits via JSON API."""

    def __init__(
        self,
        storage: IntelStorage,
        subreddits: Optional[list[str]] = None,
        limit: int = 25,
        timeframe: str = "day",
    ):
        super().__init__(storage)
        self.subreddits = subreddits or DEFAULT_SUBREDDITS
        self.limit = limit
        self.timeframe = timeframe  # hour, day, week, month, year, all
        # Reddit requires unique user agent
        self.set_client_headers(**{"User-Agent": "AI-Coach/1.0 (Personal Research Bot)"})

    @property
    def source_name(self) -> str:
        return IntelSource.REDDIT

    async def scrape(self) -> list[IntelItem]:
        """Fetch top posts from configured subreddits."""
        items = []

        for subreddit in self.subreddits:
            sub_items = await self._scrape_subreddit(subreddit)
            items.extend(sub_items)

        logger.info("Scraped %d posts from Reddit", len(items))
        return items

    @http_retry(exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.RequestError))
    async def _scrape_subreddit(self, subreddit: str) -> list[IntelItem]:
        """Fetch top posts from single subreddit."""
        url = f"https://www.reddit.com/r/{subreddit}/top.json"
        params = {"t": self.timeframe, "limit": self.limit}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return self._parse_listing(data, subreddit)
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning("Failed to fetch r/%s: %s", subreddit, e)
            return []

    def _parse_listing(self, data: dict, subreddit: str) -> list[IntelItem]:
        """Parse Reddit listing response."""
        items = []
        posts = data.get("data", {}).get("children", [])

        for post in posts:
            item = self._parse_post(post.get("data", {}), subreddit)
            if item:
                items.append(item)

        return items

    def _parse_post(self, post: dict, subreddit: str) -> Optional[IntelItem]:
        """Parse single Reddit post."""
        try:
            title = post.get("title", "")
            if not title:
                return None

            # Build URL
            permalink = post.get("permalink", "")
            url = f"https://reddit.com{permalink}" if permalink else ""

            # Selftext or link
            selftext = post.get("selftext", "")[:500]
            link_url = post.get("url", "")

            # Build summary
            score = post.get("score", 0)
            comments = post.get("num_comments", 0)
            summary_parts = [f"{score} pts", f"{comments} comments"]
            if selftext:
                summary_parts.append(selftext[:300])
            elif link_url and link_url != url:
                summary_parts.append(f"Link: {link_url}")

            # Published
            created = post.get("created_utc")
            published = datetime.fromtimestamp(created) if created else None

            # Tags
            tags = [f"r/{subreddit}"]
            if post.get("link_flair_text"):
                tags.append(post["link_flair_text"])
            tags.extend(detect_tags(title))
            if score > 500:
                tags.append("popular")
            tags = list(dict.fromkeys(tags))[:8]

            return IntelItem(
                source=f"{self.source_name}:{subreddit}",
                title=title,
                url=url,
                summary=" | ".join(summary_parts),
                content=selftext,
                published=published,
                tags=tags,
            )

        except (KeyError, TypeError, ValueError) as e:
            logger.debug("Failed to parse Reddit post: %s", e)
            return None
