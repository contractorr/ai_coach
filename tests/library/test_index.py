"""Tests for LibraryIndex with semantic and hybrid search."""

from library.embeddings import LibraryEmbeddingManager
from library.index import LibraryIndex


def _upsert_sample(index: LibraryIndex, report_id: str, title: str, body: str) -> None:
    index.upsert_item(
        report_id=report_id,
        title=title,
        source_kind="generated",
        report_type="custom",
        status="ready",
        collection=None,
        file_name=None,
        body_text=body,
        extracted_text="",
        updated_at="2026-01-01",
    )


def test_upsert_and_semantic_search(tmp_path):
    embeddings = LibraryEmbeddingManager(tmp_path / "chroma")
    index = LibraryIndex(tmp_path / "library", embedding_manager=embeddings)

    _upsert_sample(index, "r1", "Burnout Prevention", "strategies to avoid workplace exhaustion")
    _upsert_sample(index, "r2", "Python Tips", "advanced python programming patterns")

    results = index.semantic_search("tired and exhausted at work", n_results=5)
    assert len(results) >= 1
    assert results[0]["id"] == "r1"


def test_hybrid_search_with_embeddings(tmp_path):
    embeddings = LibraryEmbeddingManager(tmp_path / "chroma")
    index = LibraryIndex(tmp_path / "library", embedding_manager=embeddings)

    _upsert_sample(index, "r1", "Burnout Prevention", "strategies to avoid workplace exhaustion")
    _upsert_sample(index, "r2", "Python Tips", "advanced python programming patterns")

    results = index.hybrid_search("burnout exhaustion", limit=5)
    assert len(results) >= 1
    ids = [r["id"] for r in results]
    assert "r1" in ids


def test_hybrid_falls_back_without_embeddings(tmp_path):
    index = LibraryIndex(tmp_path / "library")  # no embedding manager
    _upsert_sample(index, "r1", "Burnout Prevention", "strategies to avoid workplace exhaustion")

    results = index.hybrid_search("burnout", limit=5)
    assert len(results) >= 1
    assert results[0]["id"] == "r1"


def test_delete_removes_embedding(tmp_path):
    embeddings = LibraryEmbeddingManager(tmp_path / "chroma")
    index = LibraryIndex(tmp_path / "library", embedding_manager=embeddings)

    _upsert_sample(index, "r1", "Test Report", "some content here")
    assert embeddings.count() == 1

    index.delete_item("r1")
    assert embeddings.count() == 0
