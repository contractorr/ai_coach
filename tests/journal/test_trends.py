"""Tests for topic trend detection."""

import numpy as np

from journal.trends import TrendDetector, _kmeans


class TestKmeans:
    """Test numpy-only KMeans implementation."""

    def test_separable_clusters(self):
        """Clearly separated clusters should be correctly identified."""
        rng = np.random.RandomState(0)
        c1 = rng.randn(30, 2) + np.array([5, 5])
        c2 = rng.randn(30, 2) + np.array([-5, -5])
        c3 = rng.randn(30, 2) + np.array([5, -5])
        data = np.vstack([c1, c2, c3])

        labels = _kmeans(data, n_clusters=3, seed=0)

        assert labels.shape == (90,)
        assert set(labels.tolist()) == {0, 1, 2}
        # All points in each original group should share a label
        assert len(set(labels[:30])) == 1
        assert len(set(labels[30:60])) == 1
        assert len(set(labels[60:])) == 1

    def test_returns_correct_dtype(self):
        data = np.random.randn(20, 4)
        labels = _kmeans(data, n_clusters=2)
        assert labels.dtype == int or np.issubdtype(labels.dtype, np.integer)

    def test_single_cluster(self):
        data = np.random.randn(10, 3)
        labels = _kmeans(data, n_clusters=1)
        assert np.all(labels == 0)


class TestTrendDetector:
    """Test clustering and trend detection."""

    def test_calc_growth_rate_increasing(self):
        """Increasing counts yield positive growth."""
        rate = TrendDetector._calc_growth_rate([1, 2, 3, 4, 5])
        assert rate > 0

    def test_calc_growth_rate_decreasing(self):
        """Decreasing counts yield negative growth."""
        rate = TrendDetector._calc_growth_rate([5, 4, 3, 2, 1])
        assert rate < 0

    def test_calc_growth_rate_stable(self):
        """Stable counts yield ~0 growth."""
        rate = TrendDetector._calc_growth_rate([3, 3, 3, 3])
        assert abs(rate) < 0.01

    def test_calc_growth_rate_empty(self):
        """Empty/zero counts return 0."""
        assert TrendDetector._calc_growth_rate([]) == 0.0
        assert TrendDetector._calc_growth_rate([0, 0, 0]) == 0.0

    def test_bucket_key_weekly(self):
        """Weekly bucket key format."""
        from datetime import datetime

        dt = datetime(2024, 1, 15)  # Monday of week 3
        key = TrendDetector._get_bucket_key(dt, "weekly")
        assert "W" in key

    def test_bucket_key_monthly(self):
        """Monthly bucket key format."""
        from datetime import datetime

        dt = datetime(2024, 3, 15)
        key = TrendDetector._get_bucket_key(dt, "monthly")
        assert key == "2024-03"

    def test_format_trends_text(self):
        """Trends format as readable text."""
        trends = [
            {"topic": "AI", "direction": "emerging", "growth_rate": 0.5, "total_entries": 10},
            {"topic": "Java", "direction": "declining", "growth_rate": -0.3, "total_entries": 5},
        ]
        text = TrendDetector._format_trends_text(trends)
        assert "AI" in text
        assert "emerging" in text
        assert "declining" in text

    def test_format_trends_empty(self):
        """Empty trends return default message."""
        text = TrendDetector._format_trends_text([])
        assert "No trends" in text

    def test_detect_trends_few_entries(self, temp_dirs):
        """Too few entries returns empty list."""
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])
        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        search = JournalSearch(storage, embeddings)
        detector = TrendDetector(search)

        trends = detector.detect_trends(days=90)
        assert trends == []

    def test_get_representative_entries(self):
        """Representative entries filtered by cluster."""
        entries = [
            {"cluster": 0, "title": "A"},
            {"cluster": 1, "title": "B"},
            {"cluster": 0, "title": "C"},
        ]
        reps = TrendDetector._get_representative_entries(entries, 0, 5)
        assert len(reps) == 2
        assert all(e["cluster"] == 0 for e in reps)

    def test_get_entries_with_timestamps_uses_real_embeddings(self, temp_dirs):
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])
        storage.create("career planning reflection 0", title="Career 0")
        storage.create("career planning reflection 1", title="Career 1")

        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        search = JournalSearch(storage, embeddings)
        search.sync_embeddings()
        detector = TrendDetector(search)

        entries = detector._get_entries_with_timestamps(days=365)

        assert len(entries) == 2
        assert {entry["title"] for entry in entries} == {"Career 0", "Career 1"}
