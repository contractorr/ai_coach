"""Tests for project discovery MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import coach_mcp.bootstrap


@pytest.fixture
def mock_components():
    components = {
        "config": {"paths": {"intel_db": "/tmp/intel.db"}},
        "config_model": MagicMock(),
        "paths": {"intel_db": "/tmp/intel.db"},
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


def test_projects_discover_uses_shared_service(mock_components):
    from coach_mcp.tools.projects import _projects_discover

    profile_storage = MagicMock()
    profile_storage.load.return_value = MagicMock()

    with patch('coach_mcp.tools.projects.get_profile_storage', return_value=profile_storage), patch(
        'coach_mcp.tools.projects.discover_matching_project_issues',
        return_value={"issues": [{"title": "Issue"}], "count": 1},
    ) as mock_discover:
        result = _projects_discover({"limit": 5, "days": 7})

    assert result["count"] == 1
    mock_discover.assert_called_once()


def test_projects_ideas_uses_shared_context_builder(mock_components):
    from coach_mcp.tools.projects import _projects_ideas

    profile_storage = MagicMock()

    with patch('coach_mcp.tools.projects.get_profile_storage', return_value=profile_storage), patch(
        'coach_mcp.tools.projects.build_project_ideas_context',
        return_value={"profile": "p", "journal_context": "j", "instruction": "i"},
    ) as mock_build:
        result = _projects_ideas({})

    assert result["journal_context"] == 'j'
    mock_build.assert_called_once_with(profile_storage=profile_storage, journal_search=mock_components['search'])


def test_projects_list_uses_shared_list_service(mock_components):
    from coach_mcp.tools.projects import _projects_list

    with patch(
        'coach_mcp.tools.projects.list_project_issues',
        return_value={"issues": [{"title": "Issue"}], "count": 1},
    ) as mock_list:
        result = _projects_list({"days": 21})

    assert result["count"] == 1
    mock_list.assert_called_once_with(mock_components['intel_storage'], days=21, limit=50, include_scraped_at=True)
