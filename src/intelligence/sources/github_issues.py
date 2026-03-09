"""GitHub Issues scraper — good-first-issue and help-wanted labels."""

import asyncio
from datetime import datetime
from typing import Optional

import structlog

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from shared_types import IntelSource

logger = structlog.get_logger()

GITHUB_SEARCH_API = "https://api.github.com/search/issues"


class GitHubIssuesScraper(BaseScraper):
    """Scrape GitHub issues matching user's skills."""

    def __init__(
        self,
        storage: IntelStorage,
        languages: Optional[list[str]] = None,
        labels: Optional[list[str]] = None,
        token: Optional[str] = None,
        embedding_manager=None,
    ):
        super().__init__(storage, embedding_manager)
        self.languages = languages or ["python"]
        self.labels = labels or ["good-first-issue", "help-wanted"]
        if token:
            self.set_client_headers(Authorization=f"token {token}")
        self.set_client_headers(Accept="application/vnd.github.v3+json")

    @property
    def source_name(self) -> str:
        return IntelSource.GITHUB_ISSUES

    async def scrape(self) -> list[IntelItem]:
        """Search GitHub for matching issues across languages."""
        tasks = []
        for lang in self.languages:
            for label in self.labels:
                tasks.append(self._search_issues(lang, label))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        items = []
        seen_urls = set()
        for result in results:
            if isinstance(result, list):
                for item in result:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        items.append(item)
            elif isinstance(result, Exception):
                logger.warning("github_issues_error", error=str(result))
        return items

    async def _search_issues(self, language: str, label: str) -> list[IntelItem]:
        """Search GitHub issues for a language+label combo."""
        query = f'label:"{label}" language:{language} state:open'
        params = {
            "q": query,
            "sort": "created",
            "order": "desc",
            "per_page": 15,
        }

        try:
            response = await self.client.get(GITHUB_SEARCH_API, params=params)
            if response.status_code == 403:
                logger.warning("github_rate_limited")
                return []
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.warning("github_search_failed", lang=language, label=label, error=str(e))
            return []

        items = []
        for issue in data.get("items", []):
            repo_name = (
                issue.get("repository_url", "").split("/repos/")[-1]
                if issue.get("repository_url")
                else ""
            )
            issue_labels = [lbl["name"] for lbl in issue.get("labels", [])]

            published = None
            if issue.get("created_at"):
                try:
                    published = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            summary_parts = [f"Repo: {repo_name}"]
            if issue_labels:
                summary_parts.append(f"Labels: {', '.join(issue_labels[:5])}")
            summary_parts.append(f"Language: {language}")
            comments = issue.get("comments", 0)
            if comments:
                summary_parts.append(f"{comments} comments")

            items.append(
                IntelItem(
                    source=IntelSource.GITHUB_ISSUES,
                    title=issue.get("title", ""),
                    url=issue.get("html_url", ""),
                    summary=" | ".join(summary_parts),
                    content=issue.get("body", "")[:500] if issue.get("body") else "",
                    published=published,
                    tags=["github-issue", label, language] + issue_labels[:3],
                )
            )

        return items
