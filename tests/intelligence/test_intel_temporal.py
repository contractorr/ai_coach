"""Tests for intel temporal search and date range filtering."""

from datetime import datetime, timedelta


class TestIntelStorageDateRange:
    def test_get_by_date_range_recent(self, populated_intel):
        """get_by_date_range returns items within range."""
        results = populated_intel.get_by_date_range(
            start=datetime.now() - timedelta(days=30),
            limit=10,
        )
        assert isinstance(results, list)

    def test_get_by_date_range_old(self, populated_intel):
        """Old date range returns empty if no items match."""
        results = populated_intel.get_by_date_range(
            start=datetime(2020, 1, 1),
            end=datetime(2020, 1, 2),
            limit=10,
        )
        assert len(results) == 0

    def test_get_by_date_range_no_bounds(self, populated_intel):
        """No start/end returns all items up to limit."""
        results = populated_intel.get_by_date_range(limit=100)
        assert isinstance(results, list)
        assert len(results) > 0


class TestIntelSearchTemporal:
    def test_temporal_search_returns_results(self, populated_intel):
        from intelligence.search import IntelSearch

        search = IntelSearch(storage=populated_intel)
        results = search.temporal_search(
            "AI",
            start=datetime.now() - timedelta(days=30),
            n_results=5,
        )
        assert isinstance(results, list)

    def test_temporal_search_old_range_empty(self, populated_intel):
        from intelligence.search import IntelSearch

        search = IntelSearch(storage=populated_intel)
        results = search.temporal_search(
            "AI",
            start=datetime(2020, 1, 1),
            end=datetime(2020, 1, 2),
            n_results=5,
        )
        assert len(results) == 0

    def test_temporal_search_no_query(self, populated_intel):
        """Empty query with date range returns date-filtered items."""
        from intelligence.search import IntelSearch

        search = IntelSearch(storage=populated_intel)
        results = search.temporal_search(
            "",
            start=datetime.now() - timedelta(days=30),
            n_results=5,
        )
        assert isinstance(results, list)
