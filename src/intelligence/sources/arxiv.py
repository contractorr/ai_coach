"""arXiv papers scraper for AI/ML research."""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import httpx
import structlog

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from intelligence.utils import detect_tags
from retry_utils import http_retry
from shared_types import IntelSource

logger = structlog.get_logger().bind(source="arxiv")

# arXiv categories for AI/ML/Software
DEFAULT_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.SE"]


class ArxivScraper(BaseScraper):
    """Async scraper for arXiv papers."""

    API_BASE = "http://export.arxiv.org/api/query"

    def __init__(
        self,
        storage: IntelStorage,
        categories: Optional[list[str]] = None,
        max_results: int = 30,
    ):
        super().__init__(storage)
        self.categories = categories or DEFAULT_CATEGORIES
        self.max_results = max_results

    @property
    def source_name(self) -> str:
        return IntelSource.ARXIV

    @http_retry(exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.RequestError))
    async def scrape(self) -> list[IntelItem]:
        """Fetch recent papers from arXiv."""
        # Build category query: cat:cs.AI OR cat:cs.LG OR ...
        cat_query = " OR ".join(f"cat:{cat}" for cat in self.categories)
        params = {
            "search_query": cat_query,
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        url = f"{self.API_BASE}?{urlencode(params)}"
        items = []

        try:
            logger.debug("Fetching arXiv: %s", url)
            response = await self.client.get(url)
            response.raise_for_status()
            items = self._parse_response(response.text)
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning("Failed to fetch arXiv: %s", e)

        logger.info("Scraped %d papers from arXiv", len(items))
        return items

    def _parse_response(self, xml_text: str) -> list[IntelItem]:
        """Parse arXiv Atom feed response."""
        items = []
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error("Failed to parse arXiv XML: %s", e)
            return []

        for entry in root.findall("atom:entry", ns):
            item = self._parse_entry(entry, ns)
            if item:
                items.append(item)

        return items

    def _parse_entry(self, entry, ns: dict) -> Optional[IntelItem]:
        """Parse single arXiv entry."""
        try:
            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else ""

            # Get abstract
            summary_elem = entry.find("atom:summary", ns)
            abstract = summary_elem.text.strip()[:500] if summary_elem is not None else ""

            # Get URL (prefer abs link)
            url = ""
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    continue
                href = link.get("href", "")
                if "/abs/" in href:
                    url = href
                    break
            if not url:
                id_elem = entry.find("atom:id", ns)
                url = id_elem.text if id_elem is not None else ""

            # Published date
            published = None
            pub_elem = entry.find("atom:published", ns)
            if pub_elem is not None and pub_elem.text:
                try:
                    published = datetime.fromisoformat(pub_elem.text.replace("Z", "+00:00"))
                except ValueError:
                    pass

            # Categories as tags
            tags = []
            for cat in entry.findall("atom:category", ns):
                term = cat.get("term", "")
                if term:
                    tags.append(term)

            # Add topic-based tags
            tags.extend(detect_tags(title))
            tags = list(dict.fromkeys(tags))[:8]

            # Authors for summary
            authors = []
            for author in entry.findall("atom:author", ns)[:3]:
                name = author.find("atom:name", ns)
                if name is not None and name.text:
                    authors.append(name.text)
            author_str = ", ".join(authors)
            if len(entry.findall("atom:author", ns)) > 3:
                author_str += " et al."

            summary = f"{author_str} | {abstract}" if author_str else abstract

            return IntelItem(
                source=self.source_name,
                title=title,
                url=url,
                summary=summary,
                content=abstract,
                published=published,
                tags=tags,
            )

        except (KeyError, TypeError, ValueError) as e:
            logger.debug("Failed to parse arXiv entry: %s", e)
            return None
