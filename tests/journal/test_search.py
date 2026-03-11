"""Tests for journal search operations."""

import frontmatter


class TestJournalSearch:
    """Test JournalSearch semantic and keyword search."""

    def test_init_with_storage(self, populated_journal, temp_dirs):
        """Test initialization with journal storage."""
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch

        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        search = JournalSearch(
            storage=populated_journal["storage"],
            embeddings=embeddings,
        )

        assert search.storage is not None
        assert search.embeddings is not None

    def test_semantic_search(self, populated_journal, temp_dirs):
        """Test semantic search returns relevant results."""
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch

        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        search = JournalSearch(
            storage=populated_journal["storage"],
            embeddings=embeddings,
        )

        # Sync embeddings first
        search.sync_embeddings()

        results = search.semantic_search("AI and programming")

        assert len(results) >= 1

    def test_keyword_search(self, populated_journal, temp_dirs):
        """Test keyword search finds matching entries."""
        from journal.search import JournalSearch

        search = JournalSearch(
            storage=populated_journal["storage"],
            embeddings=None,
        )

        results = search.keyword_search("Rust")

        assert len(results) >= 1
        assert any("Rust" in r.get("content", "") or "Rust" in r.get("title", "") for r in results)

    def test_keyword_search_no_results(self, populated_journal, temp_dirs):
        """Test keyword search with no matches."""
        from journal.search import JournalSearch

        search = JournalSearch(
            storage=populated_journal["storage"],
            embeddings=None,
        )

        results = search.keyword_search("xyznonexistent123")

        assert len(results) == 0

    def test_keyword_search_fallback_scans_older_entries(self, temp_dirs):
        from journal.search import JournalSearch
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])
        for i in range(20):
            storage.create(content=f"boring filler {i}", title=f"New {i}")

        old_match = temp_dirs["journal_dir"] / "2020-01-01_daily_old-match.md"
        post = frontmatter.Post("rareterm appears here")
        post["title"] = "Old Match"
        post["type"] = "daily"
        post["created"] = "2020-01-01T00:00:00"
        old_match.write_text(frontmatter.dumps(post), encoding="utf-8")

        search = JournalSearch(storage=storage, embeddings=None)
        results = search.keyword_search("rareterm", limit=5)

        assert [result["title"] for result in results] == ["Old Match"]

    def test_get_context_for_query(self, populated_journal, temp_dirs):
        """Test getting formatted context for RAG."""
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch

        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        search = JournalSearch(
            storage=populated_journal["storage"],
            embeddings=embeddings,
        )
        search.sync_embeddings()

        context = search.get_context_for_query("career and goals")

        assert isinstance(context, str)
        assert len(context) > 0

    def test_context_respects_char_limit(self, populated_journal, temp_dirs):
        """Test that context respects character limit."""
        from journal.search import JournalSearch

        search = JournalSearch(
            storage=populated_journal["storage"],
            embeddings=None,
        )

        context = search.get_context_for_query("test", max_chars=100)

        assert len(context) <= 150  # Some buffer for formatting

    def test_sync_embeddings(self, populated_journal, temp_dirs):
        """Test syncing embeddings from storage."""
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch

        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        search = JournalSearch(
            storage=populated_journal["storage"],
            embeddings=embeddings,
        )

        added, removed = search.sync_embeddings()

        assert added >= 3  # Our sample entries
        assert embeddings.count() >= 3

    def test_fallback_to_keyword_without_embeddings(self, populated_journal):
        """Test that search falls back to keyword without embeddings."""
        from journal.search import JournalSearch

        search = JournalSearch(
            storage=populated_journal["storage"],
            embeddings=None,
        )

        # Should not raise, falls back to keyword search
        results = search.semantic_search("programming")

        assert isinstance(results, list)
