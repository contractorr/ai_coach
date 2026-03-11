"""Tests for intelligence scraper and storage."""

import sqlite3
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from db import wal_connect


class TestIntelStorage:
    """Test IntelStorage SQLite operations."""

    def test_init_creates_db(self, temp_dirs):
        """Test that initialization creates database."""
        from intelligence.scraper import IntelStorage

        IntelStorage(temp_dirs["intel_db"])

        assert temp_dirs["intel_db"].exists()

    def test_save_item(self, temp_dirs):
        """Test saving an intel item returns row ID."""
        from intelligence.scraper import IntelItem, IntelStorage

        storage = IntelStorage(temp_dirs["intel_db"])

        item = IntelItem(
            source="test",
            title="Test Article",
            url="https://example.com/test",
            summary="Test summary",
        )

        result = storage.save(item)

        assert result is not None
        assert isinstance(result, int)

    def test_save_duplicate_url_ignored(self, temp_dirs):
        """Test that duplicate URLs are ignored."""
        from intelligence.scraper import IntelItem, IntelStorage

        storage = IntelStorage(temp_dirs["intel_db"])

        item = IntelItem(
            source="test",
            title="Original Title",
            url="https://example.com/unique",
            summary="Original summary",
        )

        first = storage.save(item)
        second = storage.save(item)  # Same URL

        assert first is not None
        assert second is None

    def test_get_recent(self, populated_intel):
        """Test getting recent items."""
        items = populated_intel.get_recent(days=7)

        assert len(items) >= 3

    def test_get_recent_with_limit(self, populated_intel):
        """Test get_recent respects limit."""
        items = populated_intel.get_recent(days=7, limit=1)

        assert len(items) == 1

    def test_search(self, populated_intel):
        """Test keyword search."""
        results = populated_intel.search("AI")

        assert len(results) >= 1
        assert any("AI" in r["title"] or "AI" in r["summary"] for r in results)

    def test_search_no_results(self, populated_intel):
        """Test search with no matches."""
        results = populated_intel.search("xyznonexistent")

        assert len(results) == 0

    def test_tags_stored_correctly(self, temp_dirs):
        """Test that tags are stored and retrieved."""
        from intelligence.scraper import IntelItem, IntelStorage

        storage = IntelStorage(temp_dirs["intel_db"])

        item = IntelItem(
            source="test",
            title="Tagged Item",
            url="https://example.com/tagged",
            summary="Has tags",
            tags=["python", "ai", "testing"],
        )

        storage.save(item)
        results = storage.search("Tagged")

        assert len(results) >= 1
        assert "python" in results[0]["tags"]


class TestIntelItem:
    """Test IntelItem dataclass."""

    def test_create_minimal(self):
        """Test creating item with minimal fields."""
        from intelligence.scraper import IntelItem

        item = IntelItem(
            source="test",
            title="Title",
            url="https://example.com",
            summary="Summary",
        )

        assert item.source == "test"
        assert item.content is None
        assert item.tags is None

    def test_create_full(self):
        """Test creating item with all fields."""
        from intelligence.scraper import IntelItem

        item = IntelItem(
            source="hackernews",
            title="Full Item",
            url="https://example.com/full",
            summary="Full summary",
            content="Full content body",
            published=datetime.now(),
            tags=["tag1", "tag2"],
        )

        assert item.content == "Full content body"
        assert len(item.tags) == 2


class TestSemanticDedup:
    """Test semantic dedup in save_items."""

    @pytest.mark.asyncio
    async def test_dedup_threshold_respected(self, temp_dirs):
        """save_items passes custom threshold to find_similar."""
        from intelligence.scraper import BaseScraper, IntelItem, IntelStorage

        storage = IntelStorage(temp_dirs["intel_db"])
        mock_em = MagicMock()
        mock_em.find_similar.return_value = None

        class DummyScraper(BaseScraper):
            @property
            def source_name(self):
                return "test"

            async def scrape(self):
                return []

        scraper = DummyScraper(storage, embedding_manager=mock_em)
        items = [
            IntelItem(source="test", title="Item 1", url="https://a.com/1", summary="s1"),
        ]
        await scraper.save_items(items, dedup_threshold=0.75)
        mock_em.find_similar.assert_called_once_with("Item 1 s1", threshold=0.75)

    @pytest.mark.asyncio
    async def test_dedup_marks_canonical(self, temp_dirs):
        """Items detected as similar are saved but marked as duplicates."""
        from intelligence.scraper import BaseScraper, IntelItem, IntelStorage

        storage = IntelStorage(temp_dirs["intel_db"])
        mock_em = MagicMock()
        mock_em.find_similar.return_value = "42"  # canonical Chroma doc ID

        class DummyScraper(BaseScraper):
            @property
            def source_name(self):
                return "test"

            async def scrape(self):
                return []

        scraper = DummyScraper(storage, embedding_manager=mock_em)
        items = [
            IntelItem(source="test", title="Dup", url="https://a.com/dup", summary="s"),
        ]
        new_count, deduped_count = await scraper.save_items(items)
        assert new_count == 0
        assert deduped_count == 1

        # Verify duplicate_of is set in DB
        with wal_connect(storage.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT duplicate_of FROM intel_items WHERE url = ?", ("https://a.com/dup",)
            ).fetchone()
            assert row is not None
            assert row["duplicate_of"] == 42

    @pytest.mark.asyncio
    async def test_intra_batch_dedup(self, temp_dirs):
        """Second item in batch detects first via Chroma add_item."""
        from intelligence.scraper import BaseScraper, IntelItem, IntelStorage

        storage = IntelStorage(temp_dirs["intel_db"])
        mock_em = MagicMock()
        # First call: no match. Second call: match found (first item's row ID).
        mock_em.find_similar.side_effect = [None, "1"]

        class DummyScraper(BaseScraper):
            @property
            def source_name(self):
                return "test"

            async def scrape(self):
                return []

        scraper = DummyScraper(storage, embedding_manager=mock_em)
        items = [
            IntelItem(
                source="test", title="Original", url="https://a.com/1", summary="story about AI"
            ),
            IntelItem(
                source="test", title="Duplicate", url="https://a.com/2", summary="story about AI"
            ),
        ]
        new_count, deduped_count = await scraper.save_items(items)
        assert new_count == 1
        assert deduped_count == 1

        # First item should have been indexed via add_item for intra-batch detection
        mock_em.add_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_items_returns_tuple(self, temp_dirs):
        """save_items returns (new, deduped) tuple."""
        from intelligence.scraper import BaseScraper, IntelItem, IntelStorage

        storage = IntelStorage(temp_dirs["intel_db"])

        class DummyScraper(BaseScraper):
            @property
            def source_name(self):
                return "test"

            async def scrape(self):
                return []

        scraper = DummyScraper(storage)
        items = [
            IntelItem(source="test", title="A", url="https://a.com/a", summary="s"),
        ]
        result = await scraper.save_items(items, semantic_dedup=False)
        assert isinstance(result, tuple)
        assert result == (1, 0)

    @pytest.mark.asyncio
    async def test_get_recent_excludes_duplicates(self, temp_dirs):
        """get_recent filters out items with duplicate_of set."""
        from intelligence.scraper import IntelItem, IntelStorage

        storage = IntelStorage(temp_dirs["intel_db"])
        item1 = IntelItem(source="test", title="Original", url="https://a.com/1", summary="s")
        item2 = IntelItem(source="test", title="Dup", url="https://a.com/2", summary="s2")

        row1 = storage.save(item1)
        row2 = storage.save(item2)
        assert row1 and row2

        storage.mark_duplicate(row2, row1)

        recent = storage.get_recent(days=7)
        urls = {r["url"] for r in recent}
        assert "https://a.com/1" in urls
        assert "https://a.com/2" not in urls


def test_sync_embeddings_excludes_semantic_duplicates(temp_dirs):
    from intelligence.scraper import IntelItem, IntelStorage
    from intelligence.search import IntelSearch

    storage = IntelStorage(temp_dirs["intel_db"])
    original_id = storage.save(
        IntelItem(source="test", title="Original", url="https://a.com/1", summary="s1")
    )
    duplicate_id = storage.save(
        IntelItem(source="test", title="Duplicate", url="https://a.com/2", summary="s2")
    )

    assert original_id and duplicate_id
    storage.mark_duplicate(duplicate_id, original_id)

    mock_embeddings = MagicMock()
    mock_embeddings.sync_from_storage.return_value = (1, 0)

    search = IntelSearch(storage, embedding_manager=mock_embeddings)
    result = search.sync_embeddings()

    assert result == (1, 0)
    synced_items = mock_embeddings.sync_from_storage.call_args.args[0]
    assert [item["id"] for item in synced_items] == [str(original_id)]
