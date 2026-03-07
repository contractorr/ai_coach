"""Web search abstraction for research."""

import os
from dataclasses import dataclass
from typing import Optional

import httpx
import structlog

from rate_limit import TokenBucketRateLimiter

logger = structlog.get_logger()


@dataclass
class SearchResult:
    """Single search result."""

    title: str
    url: str
    content: str
    score: float = 0.0


class WebSearchClient:
    """Abstract web search client (Tavily implementation)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "tavily",
        max_results: int = 8,
        max_content_chars: int = 3000,
    ):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.provider = provider
        self.max_results = max_results
        self.max_content_chars = max_content_chars
        self.client = httpx.Client(timeout=30.0)
        self._closed = False

        # Rate limiting
        self._limiter = TokenBucketRateLimiter(requests_per_second=1.0, burst=1)

    def search(self, query: str, search_depth: str = "advanced") -> list[SearchResult]:
        """Search for a topic and return results.

        Args:
            query: Search query
            search_depth: "basic" or "advanced"

        Returns:
            List of SearchResult with extracted content
        """
        self._rate_limit()

        if self.provider == "tavily" and self.api_key:
            return self._tavily_search(query, search_depth)
        elif self.provider == "duckduckgo" or not self.api_key:
            if not self.api_key:
                logger.info("No TAVILY_API_KEY, falling back to DuckDuckGo")
            return self._duckduckgo_search(query)
        else:
            logger.error("Unknown search provider: %s", self.provider)
            return []

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        self._limiter.acquire_sync()

    def _tavily_search(self, query: str, search_depth: str) -> list[SearchResult]:
        """Execute Tavily API search."""
        try:
            response = self.client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": search_depth,
                    "include_answer": True,
                    "include_raw_content": False,
                    "max_results": self.max_results,
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                content = item.get("content", "")[: self.max_content_chars]
                results.append(
                    SearchResult(
                        title=item.get("title", "Untitled"),
                        url=item.get("url", ""),
                        content=content,
                        score=item.get("score", 0.0),
                    )
                )

            logger.info("Tavily search for '%s' returned %d results", query, len(results))
            return results

        except httpx.HTTPStatusError as e:
            logger.error("Tavily API error %d: %s", e.response.status_code, e.response.text)
            return []
        except httpx.RequestError as e:
            logger.error("Tavily request failed: %s", e)
            return []
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            logger.error("Unexpected error in Tavily search: %s", e)
            return []

    def _duckduckgo_search(self, query: str) -> list[SearchResult]:
        """Search via DuckDuckGo HTML (no API key needed)."""
        try:
            response = self.client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (compatible; stewardme/0.1)"},
            )
            response.raise_for_status()

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, "html.parser")

            results = []
            for item in soup.select(".result")[: self.max_results]:
                title_el = item.select_one(".result__a")
                snippet_el = item.select_one(".result__snippet")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                url = title_el.get("href", "")
                content = snippet_el.get_text(strip=True) if snippet_el else ""

                if title and url:
                    results.append(
                        SearchResult(
                            title=title,
                            url=url,
                            content=content[: self.max_content_chars],
                            score=0.5,
                        )
                    )

            logger.info("DuckDuckGo search for '%s' returned %d results", query, len(results))
            return results

        except Exception as e:
            logger.error("DuckDuckGo search failed: %s", e)
            return []

    def close(self):
        """Close the HTTP client."""
        if self._closed:
            return
        self.client.close()
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncWebSearchClient:
    """Async version of web search client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "tavily",
        max_results: int = 8,
        max_content_chars: int = 3000,
    ):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.provider = provider
        self.max_results = max_results
        self.max_content_chars = max_content_chars
        self.client = httpx.AsyncClient(timeout=30.0)
        self._closed = False

    async def search(self, query: str, search_depth: str = "advanced") -> list[SearchResult]:
        """Async search for a topic."""
        if self.provider == "tavily" and self.api_key:
            return await self._tavily_search(query, search_depth)
        elif self.provider == "duckduckgo" or not self.api_key:
            if not self.api_key:
                logger.info("No TAVILY_API_KEY, falling back to DuckDuckGo")
            return await self._duckduckgo_search(query)
        return []

    async def _duckduckgo_search(self, query: str) -> list[SearchResult]:
        """Async DuckDuckGo search (no API key needed)."""
        try:
            response = await self.client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (compatible; stewardme/0.1)"},
            )
            response.raise_for_status()

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, "html.parser")

            results = []
            for item in soup.select(".result")[: self.max_results]:
                title_el = item.select_one(".result__a")
                snippet_el = item.select_one(".result__snippet")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                url = title_el.get("href", "")
                content = snippet_el.get_text(strip=True) if snippet_el else ""
                if title and url:
                    results.append(
                        SearchResult(
                            title=title,
                            url=url,
                            content=content[: self.max_content_chars],
                            score=0.5,
                        )
                    )
            return results
        except Exception as e:
            logger.error("Async DuckDuckGo search failed: %s", e)
            return []

    async def _tavily_search(self, query: str, search_depth: str) -> list[SearchResult]:
        """Execute async Tavily API search."""
        try:
            response = await self.client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": search_depth,
                    "include_answer": True,
                    "include_raw_content": False,
                    "max_results": self.max_results,
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                content = item.get("content", "")[: self.max_content_chars]
                results.append(
                    SearchResult(
                        title=item.get("title", "Untitled"),
                        url=item.get("url", ""),
                        content=content,
                        score=item.get("score", 0.0),
                    )
                )

            return results

        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            logger.error("Async Tavily search failed: %s", e)
            return []

    async def close(self):
        """Close async client."""
        if self._closed:
            return
        await self.client.aclose()
        self._closed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
