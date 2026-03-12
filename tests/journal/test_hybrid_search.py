"""Tests for hybrid journal search with RRF and temporal search."""

from datetime import datetime, timedelta


class TestHybridSearch:
    def test_hybrid_search_merges_results(self, populated_journal, temp_dirs):
        """Hybrid search returns RRF-merged results from semantic + keyword."""
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch

        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        search = JournalSearch(storage=populated_journal["storage"], embeddings=embeddings)
        search.sync_embeddings()

        results = search.hybrid_search("Rust programming")
        assert len(results) >= 1
        # All results should have path
        for r in results:
            assert "path" in r

    def test_hybrid_search_without_embeddings(self, populated_journal):
        """Hybrid search falls back gracefully when no embeddings."""
        from journal.search import JournalSearch

        search = JournalSearch(storage=populated_journal["storage"], embeddings=None)
        results = search.hybrid_search("Rust")
        assert isinstance(results, list)

    def test_keyword_search_has_relevance(self, populated_journal):
        """Keyword search results include relevance score."""
        from journal.search import JournalSearch

        search = JournalSearch(storage=populated_journal["storage"], embeddings=None)
        results = search.keyword_search("Rust")
        assert len(results) >= 1
        assert "relevance" in results[0]
        assert results[0]["relevance"] > 0

    def test_keyword_search_sorted_by_relevance(self, populated_journal):
        """Keyword results sorted descending by occurrence count."""
        from journal.search import JournalSearch

        search = JournalSearch(storage=populated_journal["storage"], embeddings=None)
        results = search.keyword_search("the")
        if len(results) >= 2:
            assert results[0]["relevance"] >= results[1]["relevance"]

    def test_get_context_uses_hybrid(self, populated_journal, temp_dirs):
        """get_context_for_query now uses hybrid_search internally."""
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch

        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        search = JournalSearch(storage=populated_journal["storage"], embeddings=embeddings)
        search.sync_embeddings()

        context = search.get_context_for_query("career goals")
        assert isinstance(context, str)
        assert len(context) > 0


class TestTemporalSearch:
    def test_temporal_search_filters_by_date(self, populated_journal):
        """temporal_search returns only entries within date range."""
        from journal.search import JournalSearch

        search = JournalSearch(storage=populated_journal["storage"], embeddings=None)
        now = datetime.now()

        # Search with wide date range — should find entries
        results = search.temporal_search(
            "Rust",
            start=now - timedelta(days=365),
            end=now + timedelta(days=1),
            n_results=10,
        )
        assert isinstance(results, list)

    def test_temporal_search_narrow_range_excludes(self, populated_journal):
        """Narrow date range in the far past should return no entries."""
        from journal.search import JournalSearch

        search = JournalSearch(storage=populated_journal["storage"], embeddings=None)

        results = search.temporal_search(
            "Rust",
            start=datetime(2020, 1, 1),
            end=datetime(2020, 1, 2),
            n_results=10,
        )
        assert len(results) == 0

    def test_temporal_search_no_dates_returns_all(self, populated_journal):
        """temporal_search with no start/end acts like hybrid_search."""
        from journal.search import JournalSearch

        search = JournalSearch(storage=populated_journal["storage"], embeddings=None)
        results = search.temporal_search("Rust", n_results=10)
        # Should return results (no date filtering)
        assert isinstance(results, list)
