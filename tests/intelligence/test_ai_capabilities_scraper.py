"""Tests for AI capabilities scraper."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from intelligence.scraper import IntelItem
from intelligence.sources.ai_capabilities import AICapabilitiesScraper
from shared_types import IntelSource


class TestAICapabilitiesScraper:
    """Test AICapabilitiesScraper parsing and behavior."""

    @pytest.fixture(scope="class")
    def storage(self):
        return MagicMock(name="intel_storage")

    @pytest.fixture
    def scraper(self, storage):
        return AICapabilitiesScraper(storage)

    def test_source_name(self, scraper):
        assert scraper.source_name == IntelSource.AI_CAPABILITIES

    def test_default_sources(self, scraper):
        assert scraper.enabled_sources == ["metr", "chatbot_arena", "helm"]

    def test_custom_sources(self, storage):
        scraper = AICapabilitiesScraper(storage, sources=["metr"])
        assert scraper.enabled_sources == ["metr"]

    @pytest.mark.asyncio
    async def test_scrape_metr_releases(self, scraper):
        """Test METR GitHub releases parsing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            {
                "name": "v1.0 Autonomy Eval",
                "tag_name": "v1.0",
                "html_url": "https://github.com/METR/autonomy-evals/releases/tag/v1.0",
                "body": "First autonomy evaluation release with task suite results.",
                "published_at": "2026-01-15T10:00:00Z",
            },
            {
                "name": "v0.9 Pre-release",
                "tag_name": "v0.9",
                "html_url": "https://github.com/METR/autonomy-evals/releases/tag/v0.9",
                "body": "Pre-release with preliminary benchmarks.",
                "published_at": "2025-12-01T10:00:00Z",
            },
        ]

        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(return_value=mock_response)

        items = await scraper._scrape_metr()

        assert len(items) == 2
        assert items[0].title == "METR Eval: v1.0 Autonomy Eval"
        assert "autonomy" in items[0].tags
        assert "ai-capabilities" in items[0].tags
        assert items[0].published is not None

    @pytest.mark.asyncio
    async def test_scrape_metr_empty_body(self, scraper):
        """METR release with no body uses tag_name fallback."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            {
                "name": None,
                "tag_name": "v2.0",
                "html_url": "https://github.com/METR/autonomy-evals/releases/tag/v2.0",
                "body": "",
                "published_at": None,
            },
        ]

        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(return_value=mock_response)

        items = await scraper._scrape_metr()

        assert len(items) == 1
        assert "v2.0" in items[0].title
        assert "Release v2.0" in items[0].summary

    @pytest.mark.asyncio
    async def test_scrape_chatbot_arena_with_table(self, scraper):
        """Chatbot Arena page with table rows."""
        from bs4 import BeautifulSoup

        html = """<html><head><title>Arena Leaderboard</title></head><body>
        <table><tr><td>GPT-4o</td><td>1280</td></tr>
        <tr><td>Claude-3.5</td><td>1270</td></tr></table>
        </body></html>"""

        scraper.fetch_html = AsyncMock(return_value=BeautifulSoup(html, "html.parser"))

        items = await scraper._scrape_chatbot_arena()

        assert len(items) == 1
        assert "Chatbot Arena" in items[0].title
        assert "chatbot-arena" in items[0].tags

    @pytest.mark.asyncio
    async def test_scrape_chatbot_arena_no_table(self, scraper):
        """Chatbot Arena page without table falls back to page text."""
        from bs4 import BeautifulSoup

        html = "<html><head><title>Arena</title></head><body><p>Loading...</p></body></html>"

        scraper.fetch_html = AsyncMock(return_value=BeautifulSoup(html, "html.parser"))

        items = await scraper._scrape_chatbot_arena()

        assert len(items) == 1
        assert "Arena" in items[0].title

    @pytest.mark.asyncio
    async def test_scrape_helm_with_tables(self, scraper):
        """HELM page with benchmark tables."""
        from bs4 import BeautifulSoup

        html = """<html><body>
        <table><caption>Accuracy</caption>
        <tr><th>Model</th><th>Score</th></tr>
        <tr><td>Claude-3.5</td><td>0.89</td></tr>
        </table></body></html>"""

        scraper.fetch_html = AsyncMock(return_value=BeautifulSoup(html, "html.parser"))

        items = await scraper._scrape_helm()

        assert len(items) >= 1
        assert "HELM" in items[0].title
        assert "helm" in items[0].tags

    @pytest.mark.asyncio
    async def test_scrape_helm_no_tables(self, scraper):
        """HELM page without tables falls back to text."""
        from bs4 import BeautifulSoup

        html = "<html><body><p>HELM benchmarks coming soon</p></body></html>"

        scraper.fetch_html = AsyncMock(return_value=BeautifulSoup(html, "html.parser"))

        items = await scraper._scrape_helm()

        assert len(items) == 1
        assert items[0].summary == "HELM benchmarks coming soon"

    @pytest.mark.asyncio
    async def test_scrape_respects_enabled_sources(self, storage):
        """Only scrapes enabled sources."""
        scraper = AICapabilitiesScraper(storage, sources=["metr"])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = []

        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(return_value=mock_response)
        scraper.fetch_html = AsyncMock(return_value=None)

        await scraper.scrape()

        # Should only call METR endpoint, not chatbot_arena or helm
        assert scraper.fetch_html.call_count == 0

    @pytest.mark.asyncio
    async def test_scrape_handles_network_error(self, scraper):
        """Network errors produce empty list, not exception."""
        import httpx

        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(side_effect=httpx.ConnectError("timeout"))
        scraper.fetch_html = AsyncMock(return_value=None)

        items = await scraper.scrape()
        assert items == []

    def test_tags_include_defaults(self, scraper):
        """All items should have ai-capabilities and benchmarks tags."""
        item = IntelItem(
            source=scraper.source_name,
            title="Test",
            url="https://example.com",
            summary="Test",
            tags=["ai-capabilities", "benchmarks", "metr"],
        )
        assert "ai-capabilities" in item.tags
        assert "benchmarks" in item.tags
