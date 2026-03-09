"""GitHub trending repositories scraper."""

import re
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from retry_utils import http_retry
from shared_types import IntelSource


class GitHubTrendingScraper(BaseScraper):
    """Async scraper for GitHub trending repositories."""

    TRENDING_URL = "https://github.com/trending"

    def __init__(
        self,
        storage: IntelStorage,
        languages: Optional[list[str]] = None,
        timeframe: str = "daily",
    ):
        super().__init__(storage)
        self.languages = languages or ["python"]
        self.timeframe = timeframe  # daily, weekly, monthly

    @property
    def source_name(self) -> str:
        return IntelSource.GITHUB_TRENDING

    async def scrape(self) -> list[IntelItem]:
        """Scrape trending repos for configured languages."""
        items = []

        for lang in self.languages:
            lang_items = await self._scrape_language(lang)
            items.extend(lang_items)

        return items

    @http_retry(exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.RequestError))
    async def _scrape_language(self, language: str) -> list[IntelItem]:
        """Scrape trending repos for single language."""
        url = f"{self.TRENDING_URL}/{language}?since={self.timeframe}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except (httpx.HTTPStatusError, httpx.RequestError):
            return []

        items = []
        repo_articles = soup.select("article.Box-row")

        for article in repo_articles[:25]:  # Top 25 per language
            item = self._parse_repo(article, language)
            if item:
                items.append(item)

        return items

    def _parse_repo(self, article, language: str) -> Optional[IntelItem]:
        """Parse single repo article into IntelItem."""
        try:
            # Repo name and URL
            title_elem = article.select_one("h2 a")
            if not title_elem:
                return None

            repo_path = title_elem.get("href", "").strip("/")
            if not repo_path:
                return None

            repo_url = f"https://github.com/{repo_path}"
            repo_name = repo_path.replace("/", " / ")

            # Description
            desc_elem = article.select_one("p")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # Stars count
            stars = 0
            stars_elem = article.select_one("a[href$='/stargazers']")
            if stars_elem:
                stars_text = stars_elem.get_text(strip=True).replace(",", "")
                stars = int(stars_text) if stars_text.isdigit() else 0

            # Today's stars
            today_stars = 0
            today_elem = article.select_one("span.d-inline-block.float-sm-right")
            if today_elem:
                match = re.search(r"([\d,]+)\s+stars", today_elem.get_text())
                if match:
                    today_stars = int(match.group(1).replace(",", ""))

            # Build summary
            summary_parts = [f"{stars:,} stars"]
            if today_stars:
                summary_parts.append(f"+{today_stars:,} today")
            if description:
                summary_parts.append(description[:200])

            # Tags
            tags = [language, "github", "trending"]
            if stars > 10000:
                tags.append("popular")
            if today_stars > 500:
                tags.append("hot")

            # Topics from repo
            topic_elems = article.select("a.topic-tag")
            for topic in topic_elems[:3]:
                tags.append(topic.get_text(strip=True))

            return IntelItem(
                source=self.source_name,
                title=repo_name,
                url=repo_url,
                summary=" | ".join(summary_parts),
                content=description,
                published=datetime.now(),
                tags=tags[:8],
            )

        except (KeyError, TypeError, ValueError, AttributeError):
            return None
