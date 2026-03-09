"""Tests for intelligence, recommendations, and research MCP tools."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import coach_mcp.bootstrap


@pytest.fixture
def mock_components():
    intel_storage = MagicMock()
    intel_search = MagicMock()

    components = {
        "config": {"intelligence": {}, "paths": {"intel_db": "/tmp/intel.db"}},
        "config_model": MagicMock(),
        "paths": {"intel_db": Path("/tmp/intel.db")},
        "storage": MagicMock(),
        "embeddings": MagicMock(),
        "search": MagicMock(),
        "intel_storage": intel_storage,
        "intel_search": intel_search,
        "rag": MagicMock(),
        "advisor": None,
    }
    coach_mcp.bootstrap._components = components
    yield components


def test_intel_search(mock_components):
    """intel_search should call semantic_search."""
    from coach_mcp.tools.intelligence import _search

    mock_components["intel_search"].semantic_search.return_value = [
        {
            "id": 1,
            "source": "hackernews",
            "title": "AI News",
            "url": "https://example.com/ai",
            "summary": "Latest AI developments",
            "scraped_at": "2024-01-01",
            "score": 0.9,
        }
    ]

    result = _search({"query": "AI", "limit": 5})
    assert result["count"] == 1
    assert result["results"][0]["source"] == "hackernews"


def test_intel_get_recent(mock_components):
    """intel_get_recent should return recent items."""
    from coach_mcp.tools.intelligence import _get_recent

    mock_components["intel_storage"].get_recent.return_value = [
        {
            "id": 1,
            "source": "rss",
            "title": "Article",
            "url": "https://example.com",
            "summary": "Summary",
            "scraped_at": "2024-01-01",
        }
    ]

    result = _get_recent({"days": 3, "limit": 10})
    assert result["count"] == 1
    mock_components["intel_storage"].get_recent.assert_called_once_with(days=3, limit=10)


def test_intel_get_recent_source_filter(mock_components):
    """intel_get_recent should filter by source."""
    from coach_mcp.tools.intelligence import _get_recent

    mock_components["intel_storage"].get_recent.return_value = [
        {
            "id": 1,
            "source": "hackernews",
            "title": "HN",
            "url": "u1",
            "summary": "s",
            "scraped_at": "d",
        },
        {"id": 2, "source": "rss", "title": "RSS", "url": "u2", "summary": "s", "scraped_at": "d"},
    ]

    result = _get_recent({"source": "hackernews"})
    assert result["count"] == 1
    assert result["items"][0]["source"] == "hackernews"


def test_intel_scrape_now(mock_components):
    """intel_scrape_now should run scrapers and sync embeddings."""
    from coach_mcp.tools.intelligence import _scrape_now

    with patch("intelligence.scheduler.IntelScheduler") as MockSched:
        scheduler = MagicMock()
        MockSched.return_value = scheduler
        scheduler.run_now.return_value = {"hackernews": {"scraped": 5, "new": 3}}
        mock_components["intel_search"].sync_embeddings.return_value = (3, 0)

        result = _scrape_now({})
        assert result["scrape_results"]["hackernews"]["new"] == 3
        assert result["embeddings_synced"]["added"] == 3


def test_watchlist_upsert_and_list(mock_components, tmp_path):
    """Watchlist MCP tools should persist and return items."""
    from coach_mcp.tools.intelligence import _watchlist_list, _watchlist_upsert

    mock_components["paths"] = {"intel_db": tmp_path / "intel.db"}

    created = _watchlist_upsert({"label": "OpenAI", "priority": "high", "why": "career"})
    assert created["item"]["label"] == "OpenAI"

    listed = _watchlist_list({})
    assert listed["count"] == 1
    assert listed["items"][0]["label"] == "OpenAI"


def test_watchlist_delete(mock_components, tmp_path):
    """Watchlist delete should remove persisted item."""
    from coach_mcp.tools.intelligence import _watchlist_delete, _watchlist_upsert

    mock_components["paths"] = {"intel_db": tmp_path / "intel.db"}

    created = _watchlist_upsert({"label": "Anthropic"})
    item_id = created["item"]["id"]
    result = _watchlist_delete({"item_id": item_id})
    assert result["success"] is True


def test_recommendations_list(mock_components):
    """recommendations_list should return recommendations."""
    from coach_mcp.tools.recommendations import _list_recs

    mock_rec = MagicMock()
    mock_rec.id = 1
    mock_rec.category = "learning"
    mock_rec.title = "Read a book"
    mock_rec.description = "Read a technical book"
    mock_rec.rationale = "Good for growth"
    mock_rec.score = 8.5
    mock_rec.status = "suggested"
    mock_rec.created_at = "2024-01-01"

    with patch("coach_mcp.tools.recommendations._get_rec_storage") as mock_get:
        rec_storage = MagicMock()
        mock_get.return_value = rec_storage
        rec_storage.list_recent.return_value = [mock_rec]

        result = _list_recs({"limit": 10})
        assert result["count"] == 1
        assert result["recommendations"][0]["title"] == "Read a book"


def test_recommendations_update_status(mock_components):
    """recommendations_update_status should delegate to storage."""
    from coach_mcp.tools.recommendations import _update_status

    with patch("coach_mcp.tools.recommendations._get_rec_storage") as mock_get:
        rec_storage = MagicMock()
        mock_get.return_value = rec_storage
        rec_storage.update_status.return_value = True

        result = _update_status({"rec_id": 1, "status": "completed"})
        assert result["success"] is True


def test_recommendations_rate(mock_components):
    """recommendations_rate should delegate to storage."""
    from coach_mcp.tools.recommendations import _rate

    with patch("coach_mcp.tools.recommendations._get_rec_storage") as mock_get:
        rec_storage = MagicMock()
        mock_get.return_value = rec_storage
        rec_storage.add_feedback.return_value = True

        result = _rate({"rec_id": 1, "rating": 5, "comment": "Great"})
        assert result["success"] is True
        assert result["rating"] == 5


def test_recommendations_action_create(mock_components):
    """recommendations_action_create should delegate to storage."""
    from coach_mcp.tools.recommendations import _create_action

    with patch("coach_mcp.tools.recommendations._get_rec_storage") as mock_get:
        rec_storage = MagicMock()
        mock_get.return_value = rec_storage
        rec_storage.create_action_item.return_value = {"status": "accepted"}
        rec_storage.get_action_item.return_value = MagicMock(action_item={"status": "accepted"})

        result = _create_action({"rec_id": "abc123", "due_window": "today"})
        assert result["success"] is True
        assert result["action_item"]["status"] == "accepted"


def test_recommendations_action_update(mock_components):
    """recommendations_action_update should delegate to storage."""
    from coach_mcp.tools.recommendations import _update_action

    with patch("coach_mcp.tools.recommendations._get_rec_storage") as mock_get:
        rec_storage = MagicMock()
        mock_get.return_value = rec_storage
        rec_storage.update_action_item.return_value = {"status": "completed"}

        result = _update_action({"rec_id": "abc123", "status": "completed"})
        assert result["success"] is True
        assert result["action_item"]["status"] == "completed"


def test_recommendations_action_list(mock_components):
    """recommendations_action_list should return tracked actions."""
    from coach_mcp.tools.recommendations import _list_actions

    with patch("coach_mcp.tools.recommendations._get_rec_storage") as mock_get:
        rec_storage = MagicMock()
        mock_get.return_value = rec_storage
        rec_storage.list_action_items.return_value = [
            MagicMock(
                recommendation_id="abc123",
                recommendation_title="Ship MVP",
                category="projects",
                score=8.5,
                recommendation_status="in_progress",
                action_item={"status": "accepted"},
            )
        ]

        result = _list_actions({"limit": 10})
        assert result["count"] == 1
        assert result["actions"][0]["title"] == "Ship MVP"


def test_recommendations_action_weekly_plan(mock_components):
    """recommendations_action_weekly_plan should return weekly plan items."""
    from coach_mcp.tools.recommendations import _weekly_plan

    with patch("coach_mcp.tools.recommendations._get_rec_storage") as mock_get:
        rec_storage = MagicMock()
        mock_get.return_value = rec_storage
        rec_storage.build_weekly_plan.return_value = {
            "items": [
                MagicMock(
                    recommendation_id="abc123",
                    recommendation_title="Ship MVP",
                    category="projects",
                    score=8.5,
                    action_item={"status": "accepted"},
                )
            ],
            "capacity_points": 6,
            "used_points": 2,
            "remaining_points": 4,
        }

        result = _weekly_plan({"capacity_points": 6})
        assert result["used_points"] == 2
        assert result["items"][0]["title"] == "Ship MVP"


def test_research_topics(mock_components):
    """research_topics should return topic suggestions."""
    from coach_mcp.tools.research import _topics

    with patch("coach_mcp.tools.research._get_scheduler") as mock_get:
        scheduler = MagicMock()
        mock_get.return_value = scheduler
        scheduler.get_research_topics.return_value = [{"topic": "AI agents", "relevance": 0.9}]

        result = _topics({})
        assert result["count"] == 1
        assert result["topics"][0]["topic"] == "AI agents"


def test_research_run(mock_components):
    """research_run should trigger research and return results."""
    from coach_mcp.tools.research import _run

    with patch("coach_mcp.tools.research._get_scheduler") as mock_get:
        scheduler = MagicMock()
        mock_get.return_value = scheduler
        scheduler.run_research_now.return_value = [
            {
                "topic": "AI agents",
                "title": "AI Agent Report",
                "summary": "A report about AI agents",
                "sources": ["s1", "s2"],
                "saved_path": "/tmp/research.md",
            }
        ]

        result = _run({"topic": "AI agents"})
        assert result["count"] == 1
        assert result["reports"][0]["sources_count"] == 2


def test_research_run_with_dossier(mock_components):
    """research_run should forward dossier IDs."""
    from coach_mcp.tools.research import _run

    with patch("coach_mcp.tools.research._get_scheduler") as mock_get:
        scheduler = MagicMock()
        mock_get.return_value = scheduler
        scheduler.run_research_now.return_value = [
            {"topic": "AI agents", "dossier_id": "dos-1", "sources": []}
        ]

        result = _run({"dossier_id": "dos-1"})
        assert result["count"] == 1
        scheduler.run_research_now.assert_called_once_with(topic=None, dossier_id="dos-1")


def test_research_dossiers_list(mock_components):
    """research_dossiers_list should return dossier summaries."""
    from coach_mcp.tools.research import _dossiers

    with patch("coach_mcp.tools.research._get_scheduler") as mock_get:
        scheduler = MagicMock()
        mock_get.return_value = scheduler
        scheduler.list_research_dossiers.return_value = [
            {"dossier_id": "dos-1", "topic": "AI agents"}
        ]

        result = _dossiers({})
        assert result["count"] == 1
        assert result["dossiers"][0]["dossier_id"] == "dos-1"


def test_research_dossier_create(mock_components):
    """research_dossier_create should create a dossier."""
    from coach_mcp.tools.research import _create_dossier

    with patch("coach_mcp.tools.research._get_scheduler") as mock_get:
        scheduler = MagicMock()
        mock_get.return_value = scheduler
        scheduler.create_research_dossier.return_value = {
            "dossier_id": "dos-1",
            "topic": "AI agents",
        }

        result = _create_dossier({"topic": "AI agents"})
        assert result["dossier_id"] == "dos-1"
