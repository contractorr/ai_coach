"""Tests for arXiv scraper."""

from unittest.mock import MagicMock

import pytest

from intelligence.sources.arxiv import DEFAULT_CATEGORIES, ArxivScraper


class TestArxivScraper:
    @pytest.fixture(scope="class")
    def storage(self):
        return MagicMock(name="intel_storage")

    def test_source_name(self, storage):
        scraper = ArxivScraper(storage)
        assert scraper.source_name == "arxiv"

    def test_default_categories(self, storage):
        scraper = ArxivScraper(storage)
        assert scraper.categories == DEFAULT_CATEGORIES
        assert "cs.AI" in scraper.categories
        assert "cs.LG" in scraper.categories

    def test_custom_categories(self, storage):
        scraper = ArxivScraper(storage, categories=["cs.AI"])
        assert scraper.categories == ["cs.AI"]

    def test_max_results(self, storage):
        scraper = ArxivScraper(storage, max_results=10)
        assert scraper.max_results == 10

    @pytest.mark.asyncio
    async def test_context_manager(self, storage):
        async with ArxivScraper(storage) as scraper:
            assert scraper.client is not None
