"""Tests for journal API routes."""

import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch


def test_list_empty(client, auth_headers):
    res = client.get("/api/journal", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_create_entry(client, auth_headers):
    res = client.post(
        "/api/journal",
        headers=auth_headers,
        json={"content": "Test journal entry", "entry_type": "daily", "title": "Test"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Test"
    assert data["type"] == "daily"
    assert data["content"] == "Test journal entry"


def test_create_and_list(client, auth_headers):
    client.post(
        "/api/journal",
        headers=auth_headers,
        json={"content": "Entry one", "entry_type": "daily"},
    )
    client.post(
        "/api/journal",
        headers=auth_headers,
        json={"content": "Entry two", "entry_type": "reflection"},
    )
    res = client.get("/api/journal", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_create_invalid_type(client, auth_headers):
    res = client.post(
        "/api/journal",
        headers=auth_headers,
        json={"content": "Bad", "entry_type": "invalid"},
    )
    assert res.status_code == 400


def test_delete_entry(client, auth_headers):
    create_res = client.post(
        "/api/journal",
        headers=auth_headers,
        json={"content": "To delete", "entry_type": "daily", "title": "Delete Me"},
    )
    path = create_res.json()["path"]
    del_res = client.delete(f"/api/journal/{path}", headers=auth_headers)
    assert del_res.status_code == 204


def test_delete_entry_cleans_up_derived_state(client, auth_headers):
    from advisor.context_cache import ContextCache
    from advisor.greeting import cache_greeting, get_cached_greeting
    from journal.embeddings import EmbeddingManager
    from journal.extraction_receipts import ReceiptBuilder
    from journal.fts import JournalFTSIndex
    from memory.models import FactSource
    from web.deps import (
        get_receipt_store,
        get_thread_inbox_state_store,
        get_thread_store,
        get_user_paths,
        safe_user_id,
    )

    create_res = client.post(
        "/api/journal",
        headers=auth_headers,
        json={"content": "To delete", "entry_type": "daily", "title": "Delete Me"},
    )
    path = create_res.json()["path"]
    paths = get_user_paths("user-123")

    embeddings = EmbeddingManager(
        paths["chroma_dir"],
        collection_name=f"journal_{safe_user_id('user-123')}",
    )
    embeddings.add_entry(path, "To delete", {"type": "daily"})

    fts = JournalFTSIndex(paths["journal_dir"])
    fts.upsert(path, "Delete Me", "daily", "To delete", "", datetime.now().timestamp())

    mock_memory_store = MagicMock()

    thread_store = get_thread_store("user-123")
    thread = asyncio.run(thread_store.create_thread("Delete thread"))
    asyncio.run(thread_store.add_entry(thread.id, path, 0.91, datetime(2026, 1, 5)))
    inbox_state_store = get_thread_inbox_state_store("user-123")
    inbox_state_store.upsert_state(
        thread.id,
        inbox_state="research_started",
        last_action="seeded for delete test",
    )

    receipt_builder = ReceiptBuilder(get_receipt_store("user-123"))
    receipt_builder.seed_pending(path, "Delete Me")

    cache = ContextCache(paths["intel_db"].parent / "context_cache.db")
    cache_greeting("user-123", cache, "cached greeting")
    assert get_cached_greeting("user-123", cache) == "cached greeting"

    assert embeddings.count() == 1
    assert any(row["path"] == path for row in fts.search("delete"))
    assert asyncio.run(thread_store.get_threads_for_entry(path))
    assert inbox_state_store.get_state(thread.id) is not None
    assert get_receipt_store("user-123").get_by_entry(path) is not None

    with patch("web.routes.journal.get_memory_store", return_value=mock_memory_store):
        del_res = client.delete(f"/api/journal/{path}", headers=auth_headers)

    refreshed_embeddings = EmbeddingManager(
        paths["chroma_dir"],
        collection_name=f"journal_{safe_user_id('user-123')}",
    )

    assert del_res.status_code == 204
    assert refreshed_embeddings.count() == 0
    assert all(row["path"] != path for row in fts.search("delete"))
    mock_memory_store.delete_by_source.assert_called_once_with(FactSource.JOURNAL, path)
    assert asyncio.run(thread_store.get_threads_for_entry(path)) == []
    assert asyncio.run(thread_store.get_thread(thread.id)) is None
    assert inbox_state_store.get_state(thread.id) is None
    assert get_receipt_store("user-123").get_by_entry(path) is None
    assert get_cached_greeting("user-123", cache) is None


def test_create_fires_post_hooks(client, auth_headers):
    """POST /api/journal triggers embed + thread + memory hooks."""
    mock_schedule = MagicMock()
    with patch("web.routes.journal._schedule_post_create_hooks", mock_schedule):
        res = client.post(
            "/api/journal",
            headers=auth_headers,
            json={"content": "Hook test", "entry_type": "daily", "title": "Hooks"},
        )
    assert res.status_code == 201
    mock_schedule.assert_called_once()
    args = mock_schedule.call_args[0]
    assert args[0] == "user-123"  # user_id
    assert args[2] == "Hook test"  # content


def test_quick_capture_fires_post_hooks(client, auth_headers):
    """POST /api/journal/quick triggers embed + thread + memory hooks."""
    mock_schedule = MagicMock()
    with patch("web.routes.journal._schedule_post_create_hooks", mock_schedule):
        res = client.post(
            "/api/journal/quick",
            headers=auth_headers,
            json={"content": "Quick hook test"},
        )
    assert res.status_code == 201
    mock_schedule.assert_called_once()
    args = mock_schedule.call_args[0]
    assert args[0] == "user-123"


def test_post_hooks_embed_and_memory(tmp_path):
    """_run_post_create_hooks calls EmbeddingManager and MemoryPipeline."""
    import asyncio

    from web.routes.journal import _run_post_create_hooks

    mock_em = MagicMock()
    mock_em.collection.get.return_value = {"embeddings": [None]}

    mock_pipeline = MagicMock()

    user_paths = {
        "journal_dir": tmp_path / "journal",
        "chroma_dir": tmp_path / "chroma",
        "memory_db": tmp_path / "memory.db",
        "threads_db": tmp_path / "threads.db",
        "intel_db": tmp_path / "intel.db",
    }

    with (
        patch("web.routes.journal.get_user_paths", return_value=user_paths),
        patch("journal.embeddings.EmbeddingManager", return_value=mock_em),
        patch("web.routes.journal.get_config") as mock_cfg,
        patch("memory.pipeline.MemoryPipeline", return_value=mock_pipeline),
    ):
        mock_cfg.return_value.threads.enabled = True
        mock_cfg.return_value.memory.enabled = True

        asyncio.run(_run_post_create_hooks("u1", tmp_path / "entry.md", "text", {"type": "daily"}))

    mock_em.add_entry.assert_called_once()
    mock_pipeline.process_journal_entry.assert_called_once()
