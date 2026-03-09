"""Tests for Google Trends scraper."""

import sys
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from intelligence.sources.google_trends import GoogleTrendsScraper
from shared_types import IntelSource


class TestGoogleTrendsScraper:
    @pytest.fixture(scope="class")
    def storage(self):
        return MagicMock(name="intel_storage")

    @pytest.fixture
    def scraper(self, storage):
        return GoogleTrendsScraper(storage, keywords=["AI agents", "Rust"])

    def test_source_name(self, scraper):
        assert scraper.source_name == IntelSource.GOOGLE_TRENDS

    def test_default_config(self, scraper):
        assert scraper.spike_threshold == 20.0
        assert scraper.timeframe == "today 1-m"

    @pytest.mark.asyncio
    async def test_scrape_detects_spike(self, scraper):
        from intelligence.scraper import IntelItem

        mock_items = [
            IntelItem(
                source=IntelSource.GOOGLE_TRENDS,
                title="Google Trends: 'AI agents' interest spiked +55 pts",
                url="https://trends.google.com/trends/explore?q=AI%20agents",
                summary="'AI agents' interest rose from 30 to 85 (+55 points).",
                tags=["trends", "interest-spike", "ai-agents"],
            )
        ]

        with patch.object(scraper, "_query_batch", return_value=mock_items):
            items = await scraper.scrape()

        assert len(items) == 1
        assert "AI agents" in items[0].title
        assert items[0].source == IntelSource.GOOGLE_TRENDS

    @pytest.mark.asyncio
    async def test_scrape_no_spikes(self, scraper):
        with patch.object(scraper, "_query_batch", return_value=[]):
            items = await scraper.scrape()

        assert items == []

    @pytest.mark.asyncio
    async def test_scrape_pytrends_not_installed(self, storage):
        """When pytrends is not importable, scrape returns []."""
        scraper = GoogleTrendsScraper(storage, keywords=["test"])

        # Remove pytrends from sys.modules temporarily
        saved = {}
        for mod in list(sys.modules):
            if mod == "pytrends" or mod.startswith("pytrends."):
                saved[mod] = sys.modules.pop(mod)

        original_import = (
            __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__
        )

        def fail_pytrends(name, *args, **kwargs):
            if name == "pytrends" or name.startswith("pytrends."):
                raise ImportError("no pytrends")
            return original_import(name, *args, **kwargs)

        try:
            with patch("builtins.__import__", side_effect=fail_pytrends):
                items = await scraper.scrape()
            assert items == []
        finally:
            sys.modules.update(saved)

    def test_query_batch_with_spike(self, scraper):
        vals = [30] * 25 + [80, 82, 85, 88, 90]
        mock_df = pd.DataFrame({"AI agents": vals, "Rust": [50] * 30})

        mock_cls = MagicMock()
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        mock_instance.interest_over_time.return_value = mock_df

        items = scraper._query_batch(["AI agents", "Rust"], mock_cls)

        assert len(items) >= 1
        titles = [i.title for i in items]
        assert any("AI agents" in t for t in titles)

    def test_query_batch_empty_df(self, scraper):
        mock_cls = MagicMock()
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        mock_instance.interest_over_time.return_value = pd.DataFrame()

        items = scraper._query_batch(["test"], mock_cls)
        assert items == []

    @pytest.mark.asyncio
    async def test_batching_over_5_keywords(self, storage):
        keywords = ["a", "b", "c", "d", "e", "f", "g"]
        sleep_calls = []

        async def no_sleep(delay):
            sleep_calls.append(delay)

        scraper = GoogleTrendsScraper(storage, keywords=keywords, sleep_fn=no_sleep)

        call_count = 0

        def mock_query(batch, cls):
            nonlocal call_count
            call_count += 1
            return []

        with patch.object(scraper, "_query_batch", side_effect=mock_query):
            await scraper.scrape()

        assert call_count == 2  # 5 + 2 = 2 batches
        assert sleep_calls == [2.0]

    def test_query_batch_short_series(self, scraper):
        """Series with < 5 data points is skipped."""
        mock_df = pd.DataFrame({"AI agents": [50, 60, 70]})

        mock_cls = MagicMock()
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        mock_instance.interest_over_time.return_value = mock_df

        items = scraper._query_batch(["AI agents"], mock_cls)
        assert items == []
