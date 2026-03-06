"""Tests for MCP server init and tool listing."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import coach_mcp.bootstrap
import coach_mcp.server


@pytest.fixture
def mock_components():
    """Set bootstrap components directly to avoid real config/DB init."""
    components = {
        "config": {"paths": {"intel_db": "/tmp/test_intel.db"}},
        "config_model": MagicMock(),
        "paths": {"journal_dir": "/tmp/test_journal", "chroma_dir": "/tmp/test_chroma", "intel_db": Path("/tmp/test_intel.db")},
        "storage": MagicMock(),
        "embeddings": MagicMock(),
        "search": MagicMock(),
        "intel_storage": MagicMock(),
        "intel_search": MagicMock(),
        "rag": MagicMock(),
        "advisor": None,
    }
    coach_mcp.bootstrap._components = components
    # Reset tool cache
    coach_mcp.server._tool_defs = None
    coach_mcp.server._handlers = None
    yield components


def test_load_tools_returns_20(mock_components):
    """Server should register exactly 32 tools."""
    from coach_mcp.server import _load_tools

    tools, handlers = _load_tools()
    assert len(tools) == 42
    assert len(handlers) == 42


def test_load_tools_names(mock_components):
    """All expected tool names should be present."""
    from coach_mcp.server import _load_tools

    tools, handlers = _load_tools()
    names = {t.name for t in tools}

    expected = {
        "journal_get_context",
        "journal_create",
        "journal_list",
        "journal_read",
        "journal_search",
        "journal_delete",
        "goals_list",
        "goals_add",
        "goals_check_in",
        "goals_update_status",
        "goals_add_milestone",
        "goals_complete_milestone",
        "intel_search",
        "intel_get_recent",
        "intel_scrape_now",
        "events_upcoming",
        "intel_trending_radar",
        "watchlist_list",
        "watchlist_upsert",
        "watchlist_delete",
        "recommendations_list",
        "recommendations_update_status",
        "recommendations_rate",
        "research_topics",
        "research_run",
        "research_dossiers_list",
        "research_dossier_create",
        "get_reflection_prompts",
        "profile_get",
        "profile_update_field",
        "projects_discover",
        "projects_ideas",
        "projects_list",
        "get_insights",
        "get_daily_brief",
        "memory_list_facts",
        "memory_search_facts",
        "memory_delete_fact",
        "memory_get_stats",
        "threads_list",
        "threads_get_entries",
        "threads_reindex",
    }
    assert names == expected


def test_tools_have_descriptions(mock_components):
    """Every tool must have a non-empty description."""
    from coach_mcp.server import _load_tools

    tools, _ = _load_tools()
    for tool in tools:
        assert tool.description, f"Tool {tool.name} missing description"


def test_tools_have_input_schemas(mock_components):
    """Every tool must have an inputSchema with type=object."""
    from coach_mcp.server import _load_tools

    tools, _ = _load_tools()
    for tool in tools:
        assert tool.inputSchema["type"] == "object", f"Tool {tool.name} bad schema type"


@pytest.mark.asyncio
async def test_call_unknown_tool(mock_components):
    """Calling unknown tool should return error JSON."""
    # Reset tool cache
    coach_mcp.server._tool_defs = None
    coach_mcp.server._handlers = None

    from coach_mcp.server import call_tool

    result = await call_tool("nonexistent_tool", {})
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "Unknown tool" in data["error"]


@pytest.mark.asyncio
async def test_list_tools_async(mock_components):
    """list_tools should return Tool objects."""
    coach_mcp.server._tool_defs = None
    coach_mcp.server._handlers = None

    from coach_mcp.server import list_tools

    tools = await list_tools()
    assert len(tools) == 42
