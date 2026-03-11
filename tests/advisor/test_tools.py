"""Tests for advisor ToolRegistry."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from advisor.tools import build_tool_registry


@pytest.fixture
def mock_components(tmp_path):
    """Build minimal components for ToolRegistry with cheap fakes."""
    from journal.storage import JournalStorage

    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()
    intel_db = tmp_path / "intel.db"
    recs_dir = tmp_path / "recommendations"
    profile_path = tmp_path / "profile.yaml"

    storage = JournalStorage(journal_dir)
    embeddings = MagicMock(name="embeddings")
    embeddings.query.return_value = []
    embeddings.add_entry.return_value = None
    embeddings.sync_from_storage.return_value = None

    intel_storage = MagicMock(name="intel_storage")
    intel_storage.db_path = intel_db
    intel_storage.search.return_value = []
    intel_storage.get_recent.return_value = []

    rag = MagicMock(name="rag")
    rag.get_combined_context.return_value = ("", "")
    rag.get_profile_context.return_value = ""
    rag.get_recent_entries.return_value = ""
    rag.get_journal_context.return_value = ""
    rag.get_research_context.return_value = ""
    rag.build_context_for_ask.return_value = SimpleNamespace(
        journal="",
        intel="",
        profile="",
        memory="",
        thoughts="",
    )

    return {
        "storage": storage,
        "embeddings": embeddings,
        "intel_storage": intel_storage,
        "rag": rag,
        "profile_path": str(profile_path),
        "recommendations_dir": recs_dir,
    }


class TestToolRegistryInit:
    def test_creates_15_tools(self, mock_components):
        registry = build_tool_registry(mock_components)
        defs = registry.get_definitions()
        assert len(defs) == 15

    def test_tool_names(self, mock_components):
        registry = build_tool_registry(mock_components)
        names = {d.name for d in registry.get_definitions()}
        expected = {
            "journal_search",
            "journal_list",
            "journal_read",
            "journal_create",
            "goals_list",
            "goals_add",
            "goals_check_in",
            "goals_update_status",
            "goal_next_steps",
            "intel_search",
            "intel_get_recent",
            "recommendations_list",
            "profile_get",
            "get_context",
            "web_search",
        }
        assert names == expected

    def test_definitions_have_schemas(self, mock_components):
        registry = build_tool_registry(mock_components)
        for defn in registry.get_definitions():
            assert defn.name
            assert defn.description
            assert "type" in defn.input_schema


class TestToolExecution:
    def test_unknown_tool_returns_error(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("nonexistent_tool", {})
        parsed = json.loads(result)
        assert "error" in parsed

    def test_journal_list_empty(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("journal_list", {})
        parsed = json.loads(result)
        assert parsed["entries"] == []
        assert parsed["count"] == 0

    def test_journal_create_and_list(self, mock_components):
        registry = build_tool_registry(mock_components)

        # Create an entry
        result = registry.execute(
            "journal_create",
            {
                "content": "Today I learned about tool calling.",
                "title": "Tool Calling Notes",
                "entry_type": "note",
            },
        )
        parsed = json.loads(result)
        assert "path" in parsed
        assert parsed["type"] == "note"

        # List should now have 1 entry
        result = registry.execute("journal_list", {})
        parsed = json.loads(result)
        assert parsed["count"] == 1
        assert parsed["entries"][0]["title"] == "Tool Calling Notes"

    def test_journal_read(self, mock_components):
        registry = build_tool_registry(mock_components)

        # Create then read
        create_result = json.loads(
            registry.execute(
                "journal_create",
                {
                    "content": "Test content here.",
                    "title": "Read Test",
                },
            )
        )
        filename = create_result["filename"]

        result = registry.execute("journal_read", {"filename": filename})
        parsed = json.loads(result)
        assert "Test content here." in parsed["content"]

    def test_journal_read_not_found(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("journal_read", {"filename": "nonexistent.md"})
        parsed = json.loads(result)
        assert "error" in parsed

    def test_journal_read_path_traversal(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("journal_read", {"filename": "../../etc/passwd"})
        parsed = json.loads(result)
        assert "error" in parsed

    def test_goals_list_empty(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("goals_list", {})
        parsed = json.loads(result)
        assert parsed["goals"] == []

    def test_goals_add_and_list(self, mock_components):
        registry = build_tool_registry(mock_components)

        result = registry.execute(
            "goals_add",
            {
                "title": "Learn Rust",
                "description": "Study Rust programming language",
            },
        )
        parsed = json.loads(result)
        assert parsed["type"] == "goal"
        assert "path" in parsed

        result = registry.execute("goals_list", {})
        parsed = json.loads(result)
        assert parsed["count"] == 1
        assert parsed["goals"][0]["title"] == "Learn Rust"

    def test_goals_check_in(self, mock_components):
        registry = build_tool_registry(mock_components)

        # Create a goal first
        create_result = json.loads(registry.execute("goals_add", {"title": "Test Goal"}))
        goal_path = create_result["path"]

        result = registry.execute(
            "goals_check_in",
            {
                "goal_path": goal_path,
                "notes": "Making progress",
            },
        )
        parsed = json.loads(result)
        assert parsed["success"] is True

    def test_goals_update_status(self, mock_components):
        registry = build_tool_registry(mock_components)

        create_result = json.loads(registry.execute("goals_add", {"title": "Complete Goal"}))
        goal_path = create_result["path"]

        result = registry.execute(
            "goals_update_status",
            {
                "goal_path": goal_path,
                "status": "completed",
            },
        )
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert parsed["status"] == "completed"

    def test_intel_search_empty(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("intel_search", {"query": "rust"})
        parsed = json.loads(result)
        assert parsed["count"] == 0

    def test_intel_get_recent_empty(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("intel_get_recent", {"days": 7})
        parsed = json.loads(result)
        assert parsed["count"] == 0

    def test_recommendations_list_empty(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("recommendations_list", {})
        parsed = json.loads(result)
        assert parsed["count"] == 0

    def test_profile_get_no_profile(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("profile_get", {})
        parsed = json.loads(result)
        assert parsed["exists"] is False

    def test_get_context(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("get_context", {"query": "test query"})
        parsed = json.loads(result)
        assert "journal_context" in parsed
        assert "intel_context" in parsed

    def test_handler_failure_returns_result(self, mock_components):
        """Handler that fails should return result JSON, not crash."""
        registry = build_tool_registry(mock_components)
        # Check in on out-of-root path returns structured error
        result = registry.execute("goals_check_in", {"goal_path": "/nonexistent/path.md"})
        parsed = json.loads(result)
        assert parsed["error"] == "Invalid path"


class TestToolResultTruncation:
    def test_large_result_truncated(self, mock_components):
        registry = build_tool_registry(mock_components)

        # Create many entries to produce a large result
        for i in range(50):
            registry.execute(
                "journal_create",
                {
                    "content": f"Entry number {i}. " + "x" * 200,
                    "title": f"Entry {i}",
                },
            )

        result = registry.execute("journal_list", {"limit": 50})
        assert len(result) <= registry.TOOL_RESULT_MAX_CHARS
        parsed = json.loads(result)
        assert parsed["truncated"] is True


class TestEntitySearchTool:
    def test_not_registered_without_entity_store(self, mock_components):
        """intel_entity_search excluded when entity_store not in components."""
        registry = build_tool_registry(mock_components)
        names = {d.name for d in registry.get_definitions()}
        assert "intel_entity_search" not in names

    def test_registered_with_entity_store(self, mock_components):
        entity_store = MagicMock(name="entity_store")
        entity_store.search_entities.return_value = []
        mock_components["entity_store"] = entity_store
        registry = build_tool_registry(mock_components)
        names = {d.name for d in registry.get_definitions()}
        assert "intel_entity_search" in names
        assert len(registry.get_definitions()) == 16

    def test_returns_entities_with_relationships(self, mock_components):
        entity_store = MagicMock(name="entity_store")
        entity_store.search_entities.return_value = [
            {"id": 1, "name": "Acme Corp", "type": "Company", "item_count": 3},
        ]
        entity_store.get_relationships.return_value = [
            {"source_name": "Acme Corp", "target_name": "WidgetCo", "type": "COMPETES_WITH"},
        ]
        mock_components["entity_store"] = entity_store
        registry = build_tool_registry(mock_components)
        result = registry.execute("intel_entity_search", {"query": "Acme"})
        parsed = json.loads(result)
        assert parsed["count"] == 1
        assert parsed["entities"][0]["name"] == "Acme Corp"
        assert len(parsed["entities"][0]["relationships"]) == 1

    def test_type_filter_passed_through(self, mock_components):
        entity_store = MagicMock(name="entity_store")
        entity_store.search_entities.return_value = []
        mock_components["entity_store"] = entity_store
        registry = build_tool_registry(mock_components)
        registry.execute("intel_entity_search", {"query": "test", "type": "Person", "limit": 3})
        entity_store.search_entities.assert_called_once_with(
            query="test",
            entity_type="Person",
            limit=3,
        )


class TestGoalNextStepsTool:
    def test_returns_enriched_context(self, mock_components):
        registry = build_tool_registry(mock_components)

        # Create a goal
        create_result = json.loads(
            registry.execute(
                "goals_add",
                {
                    "title": "Learn Kubernetes",
                    "description": "Master k8s for production deployments",
                },
            )
        )
        goal_path = create_result["path"]

        result = registry.execute("goal_next_steps", {"goal_path": goal_path})
        parsed = json.loads(result)

        assert parsed["title"] == "Learn Kubernetes"
        assert parsed["status"] == "active"
        assert "progress_percent" in parsed
        assert "milestones" in parsed
        assert "intel_matches" in parsed
        assert "related_journal" in parsed
        assert "content" in parsed

    def test_invalid_path_returns_error(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("goal_next_steps", {"goal_path": "/nonexistent/goal.md"})
        parsed = json.loads(result)
        assert "error" in parsed

    def test_path_traversal_blocked(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("goal_next_steps", {"goal_path": "../../etc/passwd"})
        parsed = json.loads(result)
        assert "error" in parsed

    def test_goals_check_in_path_traversal_blocked(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute("goals_check_in", {"goal_path": "../../etc/passwd"})
        parsed = json.loads(result)
        assert parsed["error"] == "Invalid path"

    def test_goals_update_status_path_traversal_blocked(self, mock_components):
        registry = build_tool_registry(mock_components)
        result = registry.execute(
            "goals_update_status",
            {"goal_path": "../../etc/passwd", "status": "completed"},
        )
        parsed = json.loads(result)
        assert parsed["error"] == "Invalid path"
