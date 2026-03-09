"""Tests for RSS feed scraper."""

from unittest.mock import MagicMock

import pytest


@pytest.mark.asyncio
class TestRSSFeedScraper:
    """Test RSSFeedScraper (async)."""

    @pytest.fixture(scope="class")
    def storage(self):
        return MagicMock(name="intel_storage")

    async def test_source_name(self, storage):
        """Test source name extraction from URL."""
        from intelligence.sources.rss import RSSFeedScraper

        scraper = RSSFeedScraper(storage, "https://example.com/feed.xml")

        assert "example" in scraper.source_name
        await scraper.close()

    async def test_source_name_custom(self, storage):
        """Test custom source name."""
        from intelligence.sources.rss import RSSFeedScraper

        scraper = RSSFeedScraper(storage, "https://example.com/feed.xml", name="custom")

        assert scraper.source_name == "rss:custom"
        await scraper.close()

    async def test_extract_name_from_url(self, storage):
        """Test URL name extraction."""
        from intelligence.sources.rss import RSSFeedScraper

        scraper = RSSFeedScraper(storage, "https://www.techcrunch.com/feed/")

        assert "techcrunch" in scraper.source_name
        await scraper.close()

    async def test_context_manager(self, storage):
        """Test async context manager."""
        from intelligence.sources.rss import RSSFeedScraper

        async with RSSFeedScraper(storage, "https://example.com/feed") as scraper:
            assert "rss:" in scraper.source_name


class TestRSSTagExtraction:
    """Test RSS tag extraction utilities."""

    def test_extract_tags(self, temp_dirs):
        """Test tag extraction from feed entry."""
        from intelligence.sources.rss import _extract_entry_tags

        mock_entry = MagicMock()
        mock_tag1 = MagicMock(term="python")
        mock_tag2 = MagicMock(term="programming")
        mock_entry.tags = [mock_tag1, mock_tag2]

        tags = _extract_entry_tags(mock_entry)

        assert "python" in tags
        assert "programming" in tags

    def test_extract_tags_no_tags(self, temp_dirs):
        """Test tag extraction when entry has no tags."""
        from intelligence.sources.rss import _extract_entry_tags

        mock_entry = MagicMock(spec=[])  # No tags attribute

        tags = _extract_entry_tags(mock_entry)

        assert tags == []
