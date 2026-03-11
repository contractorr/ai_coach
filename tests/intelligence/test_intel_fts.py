"""Tests for intelligence FTS5 search."""

import sqlite3

from intelligence.scraper import IntelItem, IntelStorage


class TestIntelFTS:
    """Test FTS5 table creation, triggers, and search in IntelStorage."""

    def test_fts_table_created(self, temp_dirs):
        """FTS virtual table is created on init."""
        storage = IntelStorage(temp_dirs["intel_db"])

        with sqlite3.connect(str(storage.db_path)) as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            assert "intel_fts" in tables

    def test_triggers_created(self, temp_dirs):
        """INSERT/DELETE/UPDATE triggers exist."""
        storage = IntelStorage(temp_dirs["intel_db"])

        with sqlite3.connect(str(storage.db_path)) as conn:
            triggers = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger'"
                ).fetchall()
            ]
            assert "intel_fts_ai" in triggers
            assert "intel_fts_ad" in triggers
            assert "intel_fts_au" in triggers

    def test_auto_index_on_save(self, temp_dirs):
        """Saving an item auto-populates FTS via trigger."""
        storage = IntelStorage(temp_dirs["intel_db"])

        item = IntelItem(
            source="test",
            title="Rust Ownership Model",
            url="https://example.com/rust-ownership",
            summary="Deep dive into Rust borrow checker",
            tags=["rust", "programming"],
        )
        storage.save(item)

        results = storage.fts_search("rust")
        assert len(results) == 1
        assert results[0]["title"] == "Rust Ownership Model"

    def test_bm25_ranking(self, temp_dirs):
        """Items with more term occurrences rank higher."""
        storage = IntelStorage(temp_dirs["intel_db"])

        # Item with many mentions of "rust"
        storage.save(
            IntelItem(
                source="test",
                title="Rust Rust Rust",
                url="https://example.com/rust-many",
                summary="Rust ownership Rust borrow Rust lifetime",
                tags=["rust"],
            )
        )
        # Item with one mention
        storage.save(
            IntelItem(
                source="test",
                title="Python Tips",
                url="https://example.com/python-tips",
                summary="Some tips, also mentions Rust briefly",
                tags=["python"],
            )
        )

        results = storage.fts_search("rust", limit=2)
        assert len(results) == 2
        # First result should be the one with more rust mentions
        assert "Rust Rust" in results[0]["title"]

    def test_fts_search_empty_query(self, temp_dirs):
        storage = IntelStorage(temp_dirs["intel_db"])
        results = storage.fts_search("")
        assert results == []

    def test_fts_search_no_matches(self, temp_dirs):
        storage = IntelStorage(temp_dirs["intel_db"])
        storage.save(
            IntelItem(
                source="test",
                title="Something",
                url="https://example.com/something",
                summary="content here",
            )
        )
        results = storage.fts_search("nonexistent_xyzzy")
        assert results == []

    def test_backfill_on_reinit(self, temp_dirs):
        """Re-initializing storage backfills existing items into FTS."""
        storage = IntelStorage(temp_dirs["intel_db"])
        storage.save(
            IntelItem(
                source="test",
                title="Pre-existing Item",
                url="https://example.com/pre-existing",
                summary="Was here before FTS",
            )
        )

        # Simulate dropping FTS and re-init (backfill path)
        with sqlite3.connect(str(storage.db_path)) as conn:
            conn.execute("DROP TABLE IF EXISTS intel_fts")
            # Drop triggers too so _init_db recreates everything
            conn.execute("DROP TRIGGER IF EXISTS intel_fts_ai")
            conn.execute("DROP TRIGGER IF EXISTS intel_fts_ad")
            conn.execute("DROP TRIGGER IF EXISTS intel_fts_au")

        # Re-init triggers backfill
        storage2 = IntelStorage(temp_dirs["intel_db"])
        results = storage2.fts_search("pre-existing")
        assert len(results) == 1

    def test_to_fts5_query(self):
        assert IntelStorage._to_fts5_query("rust programming") == "rust* programming*"
        assert IntelStorage._to_fts5_query("") == ""
        assert IntelStorage._to_fts5_query("AI") == "ai*"

    def test_tags_searchable(self, temp_dirs):
        """Tags stored in FTS are searchable."""
        storage = IntelStorage(temp_dirs["intel_db"])
        storage.save(
            IntelItem(
                source="test",
                title="Generic Title",
                url="https://example.com/tags-test",
                summary="No keywords here",
                tags=["machinelearning", "deeplearning"],
            )
        )
        results = storage.fts_search("machinelearning")
        assert len(results) == 1


class TestIntelSearchFTSRouting:
    """IntelSearch.keyword_search routes through FTS."""

    def test_keyword_search_uses_fts(self, populated_intel):
        from intelligence.search import IntelSearch

        search = IntelSearch(populated_intel)
        results = search.keyword_search("AI")
        assert len(results) >= 1

    def test_keyword_search_applies_source_filter(self, populated_intel):
        from intelligence.search import IntelSearch

        search = IntelSearch(populated_intel)
        results = search.keyword_search("AI", source_filter="github_trending")

        assert results
        assert {item["source"] for item in results} == {"github_trending"}

    def test_keyword_search_applies_source_filter_in_fallback(self, populated_intel, monkeypatch):
        from intelligence.search import IntelSearch

        search = IntelSearch(populated_intel)
        monkeypatch.setattr(populated_intel, "fts_search", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("fts unavailable")))

        results = search.keyword_search("AI", source_filter="hackernews")

        assert results
        assert {item["source"] for item in results} == {"hackernews"}
