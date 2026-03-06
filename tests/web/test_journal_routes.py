"""Tests for journal API routes."""

from unittest.mock import AsyncMock, MagicMock, patch


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


def test_create_fires_post_hooks(client, auth_headers):
    """POST /api/journal triggers embed + thread + memory hooks."""
    mock_hooks = AsyncMock()
    with patch("web.routes.journal._run_post_create_hooks", mock_hooks):
        res = client.post(
            "/api/journal",
            headers=auth_headers,
            json={"content": "Hook test", "entry_type": "daily", "title": "Hooks"},
        )
    assert res.status_code == 201
    mock_hooks.assert_called_once()
    args = mock_hooks.call_args[0]
    assert args[0] == "user-123"  # user_id
    assert args[2] == "Hook test"  # content


def test_quick_capture_fires_post_hooks(client, auth_headers):
    """POST /api/journal/quick triggers embed + thread + memory hooks."""
    mock_hooks = AsyncMock()
    with patch("web.routes.journal._run_post_create_hooks", mock_hooks):
        res = client.post(
            "/api/journal/quick",
            headers=auth_headers,
            json={"content": "Quick hook test"},
        )
    assert res.status_code == 201
    mock_hooks.assert_called_once()
    args = mock_hooks.call_args[0]
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
        "intel_db": tmp_path / "intel.db",
    }

    with (
        patch("web.routes.journal.get_user_paths", return_value=user_paths),
        patch("journal.embeddings.EmbeddingManager", return_value=mock_em),
        patch("web.routes.journal.get_config") as mock_cfg,
        patch("memory.store.FactStore"),
        patch("memory.pipeline.MemoryPipeline", return_value=mock_pipeline),
    ):
        mock_cfg.return_value.threads.enabled = True
        mock_cfg.return_value.memory.enabled = True

        asyncio.run(_run_post_create_hooks("u1", tmp_path / "entry.md", "text", {"type": "daily"}))

    mock_em.add_entry.assert_called_once()
    mock_pipeline.process_journal_entry.assert_called_once()
