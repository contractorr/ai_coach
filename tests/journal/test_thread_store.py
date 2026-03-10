"""Tests for ThreadStore — SQLite-backed thread groupings."""

from datetime import datetime

import pytest

from journal.thread_store import ThreadStore


@pytest.fixture
def store(tmp_path):
    return ThreadStore(tmp_path / "threads.db")


class TestCreateAndRetrieve:
    @pytest.mark.asyncio
    async def test_create_thread(self, store):
        t = await store.create_thread("test topic")
        assert t.id
        assert t.label == "test topic"
        assert t.status == "active"
        assert t.entry_count == 0

    @pytest.mark.asyncio
    async def test_get_thread(self, store):
        t = await store.create_thread("topic")
        fetched = await store.get_thread(t.id)
        assert fetched is not None
        assert fetched.label == "topic"
        assert fetched.entry_count == 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_thread(self, store):
        assert await store.get_thread("missing") is None


class TestAddEntry:
    @pytest.mark.asyncio
    async def test_add_entry_increments_count(self, store):
        t = await store.create_thread("topic")
        await store.add_entry(t.id, "entry1", 0.85, datetime(2026, 1, 5))
        await store.add_entry(t.id, "entry2", 0.82, datetime(2026, 1, 22))

        fetched = await store.get_thread(t.id)
        assert fetched.entry_count == 2

    @pytest.mark.asyncio
    async def test_add_entry_updates_thread_timestamp(self, store):
        t = await store.create_thread("topic")
        original_updated = t.updated_at
        await store.add_entry(t.id, "entry1", 0.85, datetime(2026, 1, 5))

        fetched = await store.get_thread(t.id)
        assert fetched.updated_at >= original_updated

    @pytest.mark.asyncio
    async def test_duplicate_entry_replaces(self, store):
        t = await store.create_thread("topic")
        await store.add_entry(t.id, "entry1", 0.85, datetime(2026, 1, 5))
        await store.add_entry(t.id, "entry1", 0.90, datetime(2026, 1, 5))

        entries = await store.get_thread_entries(t.id)
        assert len(entries) == 1
        assert entries[0].similarity == 0.90

    @pytest.mark.asyncio
    async def test_strength_increases_when_entries_join(self, store):
        t = await store.create_thread("topic")
        await store.add_entry(t.id, "entry1", 0.84, datetime(2026, 1, 5))
        after_one = await store.get_thread(t.id)
        await store.add_entry(t.id, "entry2", 0.91, datetime(2026, 1, 12))
        after_two = await store.get_thread(t.id)

        assert after_one is not None
        assert after_two is not None
        assert after_two.strength > after_one.strength


class TestGetThreadsForEntry:
    @pytest.mark.asyncio
    async def test_entry_in_one_thread(self, store):
        t = await store.create_thread("topic")
        await store.add_entry(t.id, "entry1", 0.85, datetime(2026, 1, 5))

        threads = await store.get_threads_for_entry("entry1")
        assert len(threads) == 1
        assert threads[0].id == t.id

    @pytest.mark.asyncio
    async def test_entry_in_no_threads(self, store):
        threads = await store.get_threads_for_entry("orphan")
        assert threads == []


class TestActiveThreads:
    @pytest.mark.asyncio
    async def test_filters_by_min_entries(self, store):
        t1 = await store.create_thread("big topic")
        await store.add_entry(t1.id, "e1", 0.85, datetime(2026, 1, 5))
        await store.add_entry(t1.id, "e2", 0.82, datetime(2026, 1, 22))

        t2 = await store.create_thread("small topic")
        await store.add_entry(t2.id, "e3", 0.80, datetime(2026, 2, 1))

        active = await store.get_active_threads(min_entries=2)
        assert len(active) == 1
        assert active[0].id == t1.id

    @pytest.mark.asyncio
    async def test_default_min_entries_is_two(self, store):
        t = await store.create_thread("solo")
        await store.add_entry(t.id, "e1", 0.85, datetime(2026, 1, 5))

        active = await store.get_active_threads()
        assert len(active) == 0


class TestThreadEntries:
    @pytest.mark.asyncio
    async def test_entries_ordered_by_date(self, store):
        t = await store.create_thread("topic")
        await store.add_entry(t.id, "e2", 0.82, datetime(2026, 1, 22))
        await store.add_entry(t.id, "e1", 0.85, datetime(2026, 1, 5))

        entries = await store.get_thread_entries(t.id)
        assert len(entries) == 2
        assert entries[0].entry_id == "e1"
        assert entries[1].entry_id == "e2"


class TestUpdateLabel:
    @pytest.mark.asyncio
    async def test_update_label(self, store):
        t = await store.create_thread("old label")
        await store.update_label(t.id, "new label")

        fetched = await store.get_thread(t.id)
        assert fetched.label == "new label"


class TestClearAll:
    @pytest.mark.asyncio
    async def test_clear_removes_everything(self, store):
        t = await store.create_thread("topic")
        await store.add_entry(t.id, "e1", 0.85, datetime(2026, 1, 5))

        await store.clear_all()

        assert await store.get_thread(t.id) is None
        assert await store.get_active_threads() == []
