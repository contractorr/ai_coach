"""Tests for LibraryEmbeddingManager."""

from library.embeddings import LibraryEmbeddingManager

HASH_CONFIG = {"embeddings": {"provider": "hash"}}


def test_add_and_query(tmp_path):
    mgr = LibraryEmbeddingManager(tmp_path / "chroma", config=HASH_CONFIG)
    mgr.add_item("doc-1", "burnout and workplace exhaustion strategies", {"status": "ready"})

    results = mgr.query("exhaustion", n_results=5)
    assert len(results) == 1
    assert results[0]["id"] == "doc-1"
    assert results[0]["distance"] >= 0


def test_remove_item(tmp_path):
    mgr = LibraryEmbeddingManager(tmp_path / "chroma", config=HASH_CONFIG)
    mgr.add_item("doc-1", "some content")
    assert mgr.count() == 1

    mgr.remove_item("doc-1")
    assert mgr.count() == 0


def test_remove_nonexistent_no_error(tmp_path):
    mgr = LibraryEmbeddingManager(tmp_path / "chroma", config=HASH_CONFIG)
    mgr.remove_item("does-not-exist")  # should not raise


def test_sync_from_storage(tmp_path):
    mgr = LibraryEmbeddingManager(tmp_path / "chroma", config=HASH_CONFIG)
    mgr.add_item("old-1", "stale content")

    items = [
        {"id": "new-1", "content": "first doc", "metadata": {"status": "ready"}},
        {"id": "new-2", "content": "second doc"},
    ]
    added, removed = mgr.sync_from_storage(items)

    assert added == 2
    assert removed == 1
    assert mgr.count() == 2


def test_query_empty_returns_empty(tmp_path):
    mgr = LibraryEmbeddingManager(tmp_path / "chroma", config=HASH_CONFIG)
    results = mgr.query("anything")
    assert results == []


def test_unavailable_without_provider(tmp_path, monkeypatch):
    """No API keys and no explicit config → is_available=False."""
    # Override autouse fixture: make build_embedding_function return None
    monkeypatch.setattr("library.embeddings.build_embedding_function", lambda config=None: None)

    mgr = LibraryEmbeddingManager(tmp_path / "chroma")
    assert not mgr.is_available
    assert mgr.count() == 0
    assert mgr.query("anything") == []
    assert mgr.sync_from_storage([]) == (0, 0)
