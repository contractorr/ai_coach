"""Tests for Hacker News scraper."""

from unittest.mock import MagicMock

import pytest


@pytest.mark.asyncio
class TestHackerNewsScraper:
    """Test HackerNewsScraper (async)."""

    @pytest.fixture(scope="class")
    def storage(self):
        return MagicMock(name="intel_storage")

    async def test_source_name(self, storage):
        """Test source name is correct."""
        from intelligence.sources.hn import HackerNewsScraper

        scraper = HackerNewsScraper(storage)

        assert scraper.source_name == "hackernews"
        await scraper.close()

    async def test_max_stories_config(self, storage):
        """Test max stories configuration."""
        from intelligence.sources.hn import HackerNewsScraper

        scraper = HackerNewsScraper(storage, max_stories=10)

        assert scraper.max_stories == 10
        await scraper.close()

    async def test_context_manager(self, storage):
        """Test async context manager."""
        from intelligence.sources.hn import HackerNewsScraper

        async with HackerNewsScraper(storage) as scraper:
            assert scraper.source_name == "hackernews"


class TestHNTagDetection:
    """Test HN tag detection utilities."""

    def test_detect_tags_ask_hn(self, temp_dirs):
        """Test tag detection for Ask HN posts."""
        from intelligence.utils import detect_hn_tags

        tags = detect_hn_tags("Ask HN: What are the best testing frameworks?")

        assert "ask-hn" in tags

    def test_detect_tags_show_hn(self, temp_dirs):
        """Test tag detection for Show HN posts."""
        from intelligence.utils import detect_hn_tags

        tags = detect_hn_tags("Show HN: My new Python framework")

        assert "show-hn" in tags
        assert "programming" in tags

    def test_detect_tags_topics(self, temp_dirs):
        """Test topic tag detection."""
        from intelligence.utils import detect_hn_tags

        tags = detect_hn_tags("New AI startup raises $50M in funding")

        assert "ai" in tags
        assert "startup" in tags

    def test_detect_tags_rust(self, temp_dirs):
        """Test tag detection for Rust topics."""
        from intelligence.utils import detect_hn_tags

        tags = detect_hn_tags("Learning Rust for systems programming")

        assert "programming" in tags
