"""Tests for MCP bootstrap storage helpers and tool delegation."""

import asyncio
from profile.storage import ProfileStorage
from unittest.mock import MagicMock, patch

import pytest

import coach_mcp.bootstrap
from journal.thread_store import ThreadStore
from memory.models import FactCategory, FactSource, StewardFact
from memory.store import FactStore


@pytest.fixture
def mock_components(tmp_path):
    components = {
        "config": {
            "profile": {"path": str(tmp_path / "custom-profile.yaml")},
            "paths": {"intel_db": str(tmp_path / "intel.db")},
        },
        "config_model": MagicMock(),
        "paths": {
            "journal_dir": tmp_path / "journal",
            "chroma_dir": tmp_path / "chroma",
            "intel_db": tmp_path / "intel.db",
        },
        "storage": MagicMock(),
        "embeddings": MagicMock(),
        "search": MagicMock(),
        "intel_storage": MagicMock(),
        "intel_search": MagicMock(),
        "rag": MagicMock(),
        "advisor": None,
    }
    coach_mcp.bootstrap._components = components
    yield components
    coach_mcp.bootstrap._components = None


def test_bootstrap_storage_paths_use_single_user_root_and_profile_override(mock_components, tmp_path):
    paths = coach_mcp.bootstrap.get_storage_paths()

    assert paths["data_dir"] == tmp_path
    assert paths["journal_dir"] == tmp_path / "journal"
    assert paths["memory_db"] == tmp_path / "memory.db"
    assert paths["threads_db"] == tmp_path / "threads.db"
    assert paths["watchlist_path"] == tmp_path / "watchlist.json"
    assert paths["profile_path"] == tmp_path / "custom-profile.yaml"
    assert mock_components["storage_paths"] == paths


def test_profile_tool_uses_bootstrap_profile_store(mock_components, tmp_path):
    from coach_mcp.tools.profile import _profile_get, _profile_update_field

    storage = ProfileStorage(tmp_path / "custom-profile.yaml")

    with patch("coach_mcp.tools.profile.get_profile_storage", return_value=storage) as mock_get:
        updated = _profile_update_field({"field": "location", "value": "London"})
        fetched = _profile_get({})

    assert updated["success"] is True
    assert fetched["exists"] is True
    assert fetched["profile"]["location"] == "London"
    assert mock_get.call_count == 2


def test_memory_tool_uses_bootstrap_memory_store(mock_components, tmp_path):
    from coach_mcp.tools.memory import _delete_fact, _list_facts

    store = FactStore(tmp_path / "memory.db", chroma_dir=None)
    store.add(
        StewardFact(
            id="fact-1",
            text="User prefers Python for APIs",
            category=FactCategory.PREFERENCE,
            source_type=FactSource.JOURNAL,
            source_id="entry-1",
            confidence=0.9,
        )
    )

    with patch("coach_mcp.tools.memory.get_memory_store", return_value=store) as mock_get:
        listed = _list_facts({})
        deleted = _delete_fact({"fact_id": "fact-1"})

    assert listed["count"] == 1
    assert listed["facts"][0]["id"] == "fact-1"
    assert deleted["deleted"] is True
    assert mock_get.call_count == 2


def test_threads_tool_uses_bootstrap_thread_store(mock_components, tmp_path):
    from datetime import datetime

    from coach_mcp.tools.threads import _get_thread_entries, _list_threads

    store = ThreadStore(tmp_path / "threads.db")
    thread = asyncio.run(store.create_thread("Recurring planning"))
    asyncio.run(store.add_entry(thread.id, "entry-1", 0.91, datetime(2026, 3, 1)))
    asyncio.run(store.add_entry(thread.id, "entry-2", 0.83, datetime(2026, 3, 4)))

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        with patch("coach_mcp.tools.threads.get_thread_store", return_value=store) as mock_get:
            listed = _list_threads({})
            detail = _get_thread_entries({"thread_id": thread.id})
    finally:
        asyncio.set_event_loop(None)
        loop.close()

    assert listed["count"] == 1
    assert listed["threads"][0]["id"] == thread.id
    assert detail["thread"]["entry_count"] == 2
    assert [item["entry_id"] for item in detail["entries"]] == ["entry-1", "entry-2"]
    assert mock_get.call_count == 2


def test_bootstrap_shared_storage_helpers_use_canonical_paths(mock_components, tmp_path):
    intel_store = coach_mcp.bootstrap.get_intel_storage()
    rec_store = coach_mcp.bootstrap.get_recommendation_storage()
    insight_store = coach_mcp.bootstrap.get_insight_store()

    assert intel_store.db_path == tmp_path / "intel.db"
    assert rec_store.dir == tmp_path / "recommendations"
    assert insight_store.db_path == tmp_path / "intel.db"
