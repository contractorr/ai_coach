"""Tests for ThreadDetector — recurrence detection via ChromaDB similarity."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from journal.embeddings import EmbeddingManager
from journal.thread_store import ThreadStore
from journal.threads import ThreadDetector


@pytest.fixture
def store(tmp_path):
    return ThreadStore(tmp_path / "threads.db")


def _make_embeddings_mock(
    entries: dict[str, list[float]],
    documents: dict[str, str] | None = None,
    metadatas: dict[str, dict] | None = None,
):
    """Create a mock EmbeddingManager with a mock collection.

    Args:
        entries: {entry_id: embedding_vector}
        documents: {entry_id: document_text}
    """
    collection = MagicMock()
    collection.count.return_value = len(entries)

    def query_fn(query_embeddings=None, n_results=5, include=None):
        if not query_embeddings:
            return {"ids": [[]], "distances": [[]]}

        qvec = query_embeddings[0]
        scored = []
        for eid, evec in entries.items():
            dot = sum(a * b for a, b in zip(qvec, evec))
            distance = 1.0 - dot
            scored.append((eid, distance))
        scored.sort(key=lambda x: x[1])
        top = scored[:n_results]
        return {
            "ids": [[s[0] for s in top]],
            "distances": [[s[1] for s in top]],
        }

    collection.query = query_fn

    def get_fn(ids=None, include=None):
        docs = []
        embeds = []
        metas = []
        found_ids = []
        for eid in ids or []:
            if eid in entries:
                found_ids.append(eid)
                docs.append(
                    documents.get(eid, f"Content for {eid}") if documents else f"Content for {eid}"
                )
                embeds.append(entries[eid])
                metas.append((metadatas or {}).get(eid, {}))
        if ids is None:
            found_ids = list(entries.keys())
            docs = [
                documents.get(e, f"Content for {e}") if documents else f"Content for {e}"
                for e in found_ids
            ]
            embeds = [entries[e] for e in found_ids]
            metas = [(metadatas or {}).get(e, {}) for e in found_ids]
        return {
            "ids": found_ids,
            "documents": docs,
            "embeddings": embeds,
            "metadatas": metas,
        }

    collection.get = get_fn

    mock = MagicMock()
    mock.collection = collection
    return mock


class TestJoinsExistingThread:
    @pytest.mark.asyncio
    async def test_joins_thread_when_similar_entry_is_threaded(self, store):
        entries = {
            "e1": [0.9, 0.3, 0.1],
            "e2": [0.85, 0.35, 0.15],
        }
        embeddings = _make_embeddings_mock(entries)
        detector = ThreadDetector(embeddings, store, {"similarity_threshold": 0.7})

        thread = await store.create_thread("existing topic")
        await store.add_entry(thread.id, "e1", 0.9, datetime(2026, 1, 5))

        match = await detector.detect("e2", entries["e2"], datetime(2026, 1, 22))

        assert match.match_type == "joined_existing"
        assert match.thread_id == thread.id
        assert not match.is_new_thread
        assert "e1" in match.similar_entries


class TestCreatesNewThread:
    @pytest.mark.asyncio
    async def test_creates_thread_from_unthreaded_cluster(self, store):
        entries = {
            "e1": [0.9, 0.3, 0.1],
            "e2": [0.88, 0.32, 0.12],
            "e3": [0.87, 0.33, 0.11],
        }
        embeddings = _make_embeddings_mock(entries, {"e1": "Learning about distributed systems"})
        detector = ThreadDetector(embeddings, store, {"similarity_threshold": 0.7})

        match = await detector.detect("e3", entries["e3"], datetime(2026, 2, 12))

        assert match.match_type == "created_new"
        assert match.thread_id is not None
        assert match.is_new_thread

        thread = await store.get_thread(match.thread_id)
        assert thread.entry_count == 3

    @pytest.mark.asyncio
    async def test_preserves_existing_entry_dates_when_creating_new_thread(self, store):
        entries = {
            "e1": [0.9, 0.3, 0.1],
            "e2": [0.88, 0.32, 0.12],
            "e3": [0.87, 0.33, 0.11],
        }
        metadatas = {
            "e1": {"created": "2026-01-05T00:00:00"},
            "e2": {"created": "2026-01-07T00:00:00"},
            "e3": {"created": "2026-02-12T00:00:00"},
        }
        embeddings = _make_embeddings_mock(entries, metadatas=metadatas)
        detector = ThreadDetector(embeddings, store, {"similarity_threshold": 0.7})

        match = await detector.detect("e3", entries["e3"], datetime(2026, 2, 12))

        thread_entries = await store.get_thread_entries(match.thread_id)
        assert [(entry.entry_id, entry.entry_date.strftime("%Y-%m-%d")) for entry in thread_entries] == [
            ("e1", "2026-01-05"),
            ("e2", "2026-01-07"),
            ("e3", "2026-02-12"),
        ]


class TestUnthreaded:
    @pytest.mark.asyncio
    async def test_low_similarity_stays_unthreaded(self, store):
        entries = {
            "e1": [1.0, 0.0, 0.0],
            "e2": [0.0, 1.0, 0.0],
        }
        embeddings = _make_embeddings_mock(entries)
        detector = ThreadDetector(embeddings, store, {"similarity_threshold": 0.78})

        match = await detector.detect("e2", entries["e2"], datetime(2026, 1, 10))
        assert match.match_type == "unthreaded"
        assert match.thread_id is None

    @pytest.mark.asyncio
    async def test_single_similar_entry_no_thread(self, store):
        entries = {
            "e1": [0.9, 0.3, 0.1],
            "e2": [0.88, 0.32, 0.12],
        }
        embeddings = _make_embeddings_mock(entries)
        detector = ThreadDetector(
            embeddings, store, {"similarity_threshold": 0.7, "min_entries_for_thread": 3}
        )

        match = await detector.detect("e2", entries["e2"], datetime(2026, 1, 10))
        assert match.match_type == "unthreaded"

    @pytest.mark.asyncio
    async def test_empty_collection_unthreaded(self, store):
        entries = {"e1": [0.9, 0.3, 0.1]}
        embeddings = _make_embeddings_mock(entries)
        detector = ThreadDetector(embeddings, store, {"similarity_threshold": 0.7})

        match = await detector.detect("e1", entries["e1"], datetime(2026, 1, 5))
        assert match.match_type == "unthreaded"


class TestJoinsStrongestThread:
    @pytest.mark.asyncio
    async def test_joins_thread_with_highest_avg_similarity(self, store):
        entries = {
            "e1": [0.9, 0.3, 0.1],
            "e2": [0.5, 0.8, 0.1],
            "e3": [0.88, 0.32, 0.12],
        }
        embeddings = _make_embeddings_mock(entries)
        detector = ThreadDetector(embeddings, store, {"similarity_threshold": 0.5})

        thread_a = await store.create_thread("topic A")
        await store.add_entry(thread_a.id, "e1", 0.9, datetime(2026, 1, 5))

        thread_b = await store.create_thread("topic B")
        await store.add_entry(thread_b.id, "e2", 0.85, datetime(2026, 1, 10))

        match = await detector.detect("e3", entries["e3"], datetime(2026, 1, 20))
        assert match.match_type == "joined_existing"
        assert match.thread_id == thread_a.id


class TestReindex:
    @pytest.mark.asyncio
    async def test_reindex_rebuilds_threads(self, store):
        entries = {
            "e1": [0.9, 0.3, 0.1],
            "e2": [0.88, 0.32, 0.12],
            "e3": [0.87, 0.33, 0.11],
        }
        embeddings = _make_embeddings_mock(entries)
        detector = ThreadDetector(embeddings, store, {"similarity_threshold": 0.7})

        stats = await detector.reindex_all()
        assert stats["entries_processed"] == 3
        assert stats["entries_threaded"] >= 2
        assert stats["threads_created"] >= 1

        active = await store.get_active_threads()
        assert len(active) >= 1

    @pytest.mark.asyncio
    async def test_reindex_clears_old_threads(self, store):
        entries = {
            "e1": [1.0, 0.0, 0.0],
            "e2": [0.0, 1.0, 0.0],
        }
        embeddings = _make_embeddings_mock(entries)
        detector = ThreadDetector(embeddings, store, {"similarity_threshold": 0.9})

        old = await store.create_thread("old")
        await store.add_entry(old.id, "e1", 0.95, datetime(2026, 1, 1))
        await store.add_entry(old.id, "e2", 0.95, datetime(2026, 1, 2))

        await detector.reindex_all()
        active = await store.get_active_threads()
        assert len(active) == 0

    @pytest.mark.asyncio
    async def test_reindex_with_real_embedding_manager(self, temp_dirs, tmp_path):
        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        embeddings.add_entry("e1", "career planning distributed systems", {"created": "2026-01-01T00:00:00"})
        embeddings.add_entry(
            "e2",
            "career planning distributed systems next steps",
            {"created": "2026-01-02T00:00:00"},
        )
        embeddings.add_entry(
            "e3",
            "career planning distributed systems reflection",
            {"created": "2026-01-03T00:00:00"},
        )

        detector = ThreadDetector(
            embeddings,
            ThreadStore(tmp_path / "threads.db"),
            {"similarity_threshold": 0.1},
        )

        stats = await detector.reindex_all()

        assert stats["entries_processed"] == 3
        assert stats["entries_threaded"] >= 2
