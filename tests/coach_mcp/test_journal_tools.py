"""Tests for journal MCP tools."""

from pathlib import Path
from unittest.mock import MagicMock

import frontmatter
import pytest

import coach_mcp.bootstrap


@pytest.fixture
def mock_components(tmp_path):
    """Mock components with real-ish storage behavior."""
    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()

    storage = MagicMock()
    storage.journal_dir = journal_dir
    embeddings = MagicMock()
    search = MagicMock()
    rag = MagicMock()

    components = {
        "config": {},
        "config_model": MagicMock(),
        "paths": {"journal_dir": journal_dir},
        "storage": storage,
        "embeddings": embeddings,
        "search": search,
        "intel_storage": MagicMock(),
        "intel_search": MagicMock(),
        "rag": rag,
        "advisor": None,
    }
    coach_mcp.bootstrap._components = components
    yield components


def test_get_context(mock_components):
    """journal_get_context should call rag.get_full_context and return 3 context strings."""
    from coach_mcp.tools.journal import _get_context

    mock_components["rag"].get_full_context.return_value = (
        "journal ctx",
        "intel ctx",
        "research ctx",
    )

    result = _get_context({"query": "test query"})
    assert result["journal_context"] == "journal ctx"
    assert result["intel_context"] == "intel ctx"
    assert result["research_context"] == "research ctx"
    mock_components["rag"].get_full_context.assert_called_once_with(
        "test query", include_research=True
    )


def test_get_context_no_research(mock_components):
    """journal_get_context with include_research=False."""
    from coach_mcp.tools.journal import _get_context

    mock_components["rag"].get_full_context.return_value = ("j", "i", "")

    _get_context({"query": "test", "include_research": False})
    mock_components["rag"].get_full_context.assert_called_once_with("test", include_research=False)


def test_get_context_restores_rag_overrides(mock_components):
    """journal_get_context should not leak temporary RAG override values across calls."""
    from coach_mcp.tools.journal import _get_context

    mock_components["rag"].journal_weight = 0.7
    mock_components["rag"].max_context_chars = 8000
    mock_components["rag"].get_full_context.return_value = ("j", "i", "r")

    result = _get_context({"query": "test", "journal_weight": 0.2, "max_chars": 1000})

    assert result["journal_context"] == "j"
    assert mock_components["rag"].journal_weight == 0.7
    assert mock_components["rag"].max_context_chars == 8000
    mock_components["rag"].get_full_context.assert_called_once_with("test", include_research=True)


def test_create(mock_components):
    """journal_create should call storage.create and embeddings.add_entry."""
    from coach_mcp.tools.journal import _create

    fake_path = mock_components["storage"].journal_dir / "2024-01-01_daily_test.md"

    # Create a real file so frontmatter.load works
    post = frontmatter.Post("test content")
    post["title"] = "Test"
    post["type"] = "daily"
    fake_path.write_text(frontmatter.dumps(post))

    mock_components["storage"].create.return_value = fake_path

    result = _create({"content": "test content", "entry_type": "daily", "title": "Test"})

    assert result["filename"] == fake_path.name
    assert result["type"] == "daily"
    mock_components["storage"].create.assert_called_once()
    mock_components["embeddings"].add_entry.assert_called_once()


def test_create_rolls_back_file_when_embedding_sync_fails(mock_components):
    """journal_create should remove the new file if embedding sync fails."""
    from coach_mcp.tools.journal import _create

    fake_path = mock_components["storage"].journal_dir / "2024-01-01_daily_test.md"
    post = frontmatter.Post("test content")
    post["title"] = "Test"
    post["type"] = "daily"
    fake_path.write_text(frontmatter.dumps(post))

    mock_components["storage"].create.return_value = fake_path
    mock_components["storage"].delete.side_effect = lambda path: Path(path).unlink()
    mock_components["embeddings"].add_entry.side_effect = RuntimeError("embedding sync failed")

    with pytest.raises(RuntimeError, match="embedding sync failed"):
        _create({"content": "test content", "entry_type": "daily", "title": "Test"})

    assert not fake_path.exists()
    mock_components["storage"].delete.assert_called_once_with(fake_path)


def test_list(mock_components):
    """journal_list should return entries from storage."""
    from coach_mcp.tools.journal import _list

    mock_components["storage"].list_entries.return_value = [
        {
            "path": Path("/tmp/journal/test.md"),
            "title": "Test Entry",
            "type": "daily",
            "created": "2024-01-01T00:00:00",
            "tags": ["work"],
            "preview": "Some content...",
        }
    ]

    result = _list({"limit": 10})
    assert result["count"] == 1
    assert result["entries"][0]["title"] == "Test Entry"


def test_list_with_filters(mock_components):
    """journal_list should pass filters to storage."""
    from coach_mcp.tools.journal import _list

    mock_components["storage"].list_entries.return_value = []

    _list({"entry_type": "goal", "tag": "work", "limit": 5})
    mock_components["storage"].list_entries.assert_called_once_with(
        entry_type="goal", tags=["work"], limit=5
    )


def test_read_existing(mock_components):
    """journal_read should return content for existing file."""
    from coach_mcp.tools.journal import _read

    filepath = mock_components["storage"].journal_dir / "test.md"
    post = frontmatter.Post("Hello world")
    post["title"] = "Test"
    post["type"] = "daily"
    post["created"] = "2024-01-01"
    post["tags"] = ["test"]
    filepath.write_text(frontmatter.dumps(post))

    mock_components["storage"].read.return_value = frontmatter.load(filepath)

    result = _read({"filename": "test.md"})
    assert result["content"] == "Hello world"
    assert result["title"] == "Test"


def test_read_nonexistent(mock_components):
    """journal_read should return error for missing file."""
    from coach_mcp.tools.journal import _read

    result = _read({"filename": "nonexistent.md"})
    assert "error" in result


def test_read_path_traversal(mock_components):
    """journal_read should reject path traversal attempts."""
    from coach_mcp.tools.journal import _read

    result = _read({"filename": "../../etc/passwd"})
    assert "error" in result


def test_search(mock_components):
    """journal_search should call semantic_search."""
    from coach_mcp.tools.journal import _search

    mock_components["search"].semantic_search.return_value = [
        {
            "path": Path("/tmp/test.md"),
            "title": "Match",
            "type": "daily",
            "created": "2024-01-01",
            "tags": [],
            "content": "matching content",
            "relevance": 0.9,
        }
    ]

    result = _search({"query": "test", "limit": 3})
    assert result["count"] == 1
    assert result["results"][0]["relevance"] == 0.9
    mock_components["search"].semantic_search.assert_called_once_with("test", n_results=3)


def test_delete_existing(mock_components):
    """journal_delete should remove entry and embedding."""
    from coach_mcp.tools.journal import _delete

    filepath = mock_components["storage"].journal_dir / "todelete.md"
    post = frontmatter.Post("delete me")
    filepath.write_text(frontmatter.dumps(post))

    mock_components["storage"].delete.return_value = True

    result = _delete({"filename": "todelete.md"})
    assert result["deleted"] is True
    mock_components["embeddings"].remove_entry.assert_called_once_with(str(filepath))


def test_delete_path_traversal(mock_components):
    """journal_delete should reject path traversal."""
    from coach_mcp.tools.journal import _delete

    result = _delete({"filename": "../../../etc/passwd"})
    assert "error" in result
