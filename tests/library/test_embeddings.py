"""Tests for LibraryEmbeddingManager."""

from library.embeddings import LibraryEmbeddingManager


def test_add_and_query(tmp_path):
    mgr = LibraryEmbeddingManager(tmp_path / "chroma")
    mgr.add_item("doc-1", "burnout and workplace exhaustion strategies", {"status": "ready"})

    results = mgr.query("exhaustion", n_results=5)
    assert len(results) == 1
    assert results[0]["id"] == "doc-1"
    assert results[0]["distance"] >= 0


def test_remove_item(tmp_path):
    mgr = LibraryEmbeddingManager(tmp_path / "chroma")
    mgr.add_item("doc-1", "some content")
    assert mgr.count() == 1

    mgr.remove_item("doc-1")
    assert mgr.count() == 0


def test_remove_nonexistent_no_error(tmp_path):
    mgr = LibraryEmbeddingManager(tmp_path / "chroma")
    mgr.remove_item("does-not-exist")  # should not raise


def test_sync_from_storage(tmp_path):
    mgr = LibraryEmbeddingManager(tmp_path / "chroma")
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
    mgr = LibraryEmbeddingManager(tmp_path / "chroma")
    results = mgr.query("anything")
    assert results == []
