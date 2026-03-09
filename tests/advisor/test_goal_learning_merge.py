"""Tests for Phase 2: goal-learning merge — type field, milestones, migration."""

from unittest.mock import MagicMock, patch

import frontmatter
import pytest

from advisor.goals import GoalTracker, get_goal_defaults
from advisor.migrate_learning_paths import (
    _parse_modules,
    migrate_learning_paths,
    run_migration_if_needed,
)

# === Goal type field ===


class TestGoalTypeField:
    def test_defaults_general(self):
        d = get_goal_defaults()
        assert d["goal_type"] == "general"

    def test_defaults_learning(self):
        d = get_goal_defaults(goal_type="learning")
        assert d["goal_type"] == "learning"

    def test_defaults_career(self):
        d = get_goal_defaults(goal_type="career")
        assert d["goal_type"] == "career"

    def test_get_goals_includes_type(self, tmp_path):
        """Goals returned by get_goals include goal_type field."""
        jdir = tmp_path / "journal"
        jdir.mkdir()
        # Create a goal file
        goal_file = jdir / "2024-01-01_goal_test.md"
        post = frontmatter.Post("Some goal content")
        post.metadata = {
            "title": "Learn Rust",
            "entry_type": "goal",
            "goal_type": "learning",
            "status": "active",
            "created": "2024-01-01T00:00:00",
            "last_checked": "2024-01-01T00:00:00",
            "check_in_days": 14,
        }
        goal_file.write_text(frontmatter.dumps(post))

        storage = MagicMock()
        storage.list_entries.return_value = [{"path": str(goal_file)}]
        tracker = GoalTracker(storage)
        goals = tracker.get_goals()
        assert len(goals) == 1
        assert goals[0]["goal_type"] == "learning"

    def test_missing_type_defaults_general(self, tmp_path):
        """Goals without type field default to general."""
        jdir = tmp_path / "journal"
        jdir.mkdir()
        goal_file = jdir / "2024-01-01_goal_old.md"
        post = frontmatter.Post("Old goal")
        post.metadata = {
            "title": "Old Goal",
            "entry_type": "goal",
            "status": "active",
            "created": "2024-01-01T00:00:00",
            "last_checked": "2024-01-01T00:00:00",
        }
        goal_file.write_text(frontmatter.dumps(post))

        storage = MagicMock()
        storage.list_entries.return_value = [{"path": str(goal_file)}]
        tracker = GoalTracker(storage)
        goals = tracker.get_goals()
        assert goals[0]["goal_type"] == "general"

    def test_filter_by_goal_type(self, tmp_path):
        """get_goals(goal_type=...) filters correctly."""
        jdir = tmp_path / "journal"
        jdir.mkdir()

        for i, gtype in enumerate(["learning", "career", "general"]):
            f = jdir / f"2024-01-0{i + 1}_goal_{gtype}.md"
            post = frontmatter.Post(f"{gtype} goal")
            post.metadata = {
                "title": f"{gtype} goal",
                "entry_type": "goal",
                "goal_type": gtype,
                "status": "active",
                "created": f"2024-01-0{i + 1}T00:00:00",
                "last_checked": f"2024-01-0{i + 1}T00:00:00",
            }
            f.write_text(frontmatter.dumps(post))

        storage = MagicMock()
        storage.list_entries.return_value = [
            {"path": str(jdir / f"2024-01-0{i + 1}_goal_{t}.md")}
            for i, t in enumerate(["learning", "career", "general"])
        ]
        tracker = GoalTracker(storage)

        learning = tracker.get_goals(goal_type="learning")
        assert len(learning) == 1
        assert learning[0]["goal_type"] == "learning"

        career = tracker.get_goals(goal_type="career")
        assert len(career) == 1

        all_goals = tracker.get_goals()
        assert len(all_goals) == 3


# === Auto-milestone generation ===


class TestGenerateMilestones:
    def _make_goal(self, tmp_path, title="Test Goal", goal_type="general"):
        goal_file = tmp_path / "goal.md"
        post = frontmatter.Post("Goal description")
        post.metadata = {
            "title": title,
            "goal_type": goal_type,
            "status": "active",
            "created": "2024-01-01T00:00:00",
            "last_checked": "2024-01-01T00:00:00",
        }
        goal_file.write_text(frontmatter.dumps(post))
        return goal_file

    def test_generates_milestones(self, tmp_path):
        from advisor.engine import AdvisorEngine

        goal_file = self._make_goal(tmp_path, "Learn Kubernetes", "learning")

        mock_rag = MagicMock()
        mock_rag.get_profile_context.return_value = "Role: DevOps"
        mock_rag.cache = None

        with (
            patch("advisor.engine.create_llm_provider") as mock_llm,
            patch("advisor.engine.create_cheap_provider") as mock_cheap,
        ):
            mock_cheap.return_value.generate.return_value = "1. Set up local cluster\n2. Deploy first app\n3. Learn networking\n4. Master storage"
            mock_llm.return_value.provider_name = "mock"
            mock_cheap.return_value.provider_name = "mock"

            engine = AdvisorEngine(rag=mock_rag, api_key="test")
            result = engine.generate_milestones(goal_file)

        assert len(result) == 4
        assert result[0] == "Set up local cluster"

        # Verify milestones written to file
        post = frontmatter.load(goal_file)
        assert len(post.metadata.get("milestones", [])) == 4

    def test_goal_not_found(self, tmp_path):
        from advisor.engine import AdvisorEngine

        mock_rag = MagicMock()
        mock_rag.cache = None

        with (
            patch("advisor.engine.create_llm_provider"),
            patch("advisor.engine.create_cheap_provider"),
        ):
            engine = AdvisorEngine(rag=mock_rag, api_key="test")
            with pytest.raises(ValueError):
                engine.generate_milestones(tmp_path / "nonexistent.md")

    def test_llm_failure_returns_empty(self, tmp_path):
        from advisor.engine import AdvisorEngine
        from llm import LLMError as BaseLLMError

        goal_file = self._make_goal(tmp_path)

        mock_rag = MagicMock()
        mock_rag.get_profile_context.return_value = ""
        mock_rag.cache = None

        with (
            patch("advisor.engine.create_llm_provider") as mock_llm,
            patch("advisor.engine.create_cheap_provider") as mock_cheap,
        ):
            mock_cheap.return_value.generate.side_effect = BaseLLMError("LLM down")
            mock_llm.return_value.provider_name = "mock"
            mock_cheap.return_value.provider_name = "mock"

            engine = AdvisorEngine(rag=mock_rag, api_key="test")
            result = engine.generate_milestones(goal_file)

        assert result == []

    def test_parse_failure_returns_empty(self, tmp_path):
        from advisor.engine import AdvisorEngine

        goal_file = self._make_goal(tmp_path)

        mock_rag = MagicMock()
        mock_rag.get_profile_context.return_value = ""
        mock_rag.cache = None

        with (
            patch("advisor.engine.create_llm_provider") as mock_llm,
            patch("advisor.engine.create_cheap_provider") as mock_cheap,
        ):
            mock_cheap.return_value.generate.return_value = "No numbered list here."
            mock_llm.return_value.provider_name = "mock"
            mock_cheap.return_value.provider_name = "mock"

            engine = AdvisorEngine(rag=mock_rag, api_key="test")
            result = engine.generate_milestones(goal_file)

        assert result == []


# === Migration ===


class TestMigration:
    def _make_lp(self, lp_dir, skill, modules, completed=0, status="active"):
        """Create a learning path file in the given directory."""
        lp_dir.mkdir(parents=True, exist_ok=True)
        content = "\n".join(f"### Module {i + 1}: {m}" for i, m in enumerate(modules))
        post = frontmatter.Post(content)
        post.metadata = {
            "skill": skill,
            "status": status,
            "progress": round(completed / max(len(modules), 1) * 100),
            "total_modules": len(modules),
            "completed_modules": completed,
        }
        filepath = lp_dir / f"2024-01-01_{skill.lower().replace(' ', '-')}.md"
        filepath.write_text(frontmatter.dumps(post))
        return filepath

    def test_migrate_creates_goals(self, tmp_path):
        lp_dir = tmp_path / "learning_paths"
        self._make_lp(lp_dir, "Rust", ["Ownership", "Borrowing", "Lifetimes"])

        storage = MagicMock()
        storage.create.return_value = str(tmp_path / "goal.md")
        # Create the goal file so tracker can load it
        goal_file = tmp_path / "goal.md"
        post = frontmatter.Post("")
        post.metadata = {"title": "Rust", "status": "active", "milestones": []}
        goal_file.write_text(frontmatter.dumps(post))

        tracker = GoalTracker(storage)
        result = migrate_learning_paths(tmp_path, storage, tracker)

        assert result["migrated"] == 1
        assert result["errors"] == []
        storage.create.assert_called_once()
        call_kwargs = storage.create.call_args
        assert call_kwargs[1]["entry_type"] == "goal"
        assert call_kwargs[1]["title"] == "Rust"

    def test_migrate_missing_dir(self, tmp_path):
        storage = MagicMock()
        tracker = GoalTracker(storage)
        result = migrate_learning_paths(tmp_path, storage, tracker)
        assert result["migrated"] == 0

    def test_migration_idempotent(self, tmp_path):
        lp_dir = tmp_path / "learning_paths"
        self._make_lp(lp_dir, "Go", ["Goroutines"])

        storage = MagicMock()
        storage.create.return_value = str(tmp_path / "goal.md")
        goal_file = tmp_path / "goal.md"
        post = frontmatter.Post("")
        post.metadata = {"title": "Go", "status": "active", "milestones": []}
        goal_file.write_text(frontmatter.dumps(post))

        tracker = GoalTracker(storage)

        result1 = run_migration_if_needed(tmp_path, storage, tracker)
        assert result1 is not None
        assert result1["migrated"] == 1

        result2 = run_migration_if_needed(tmp_path, storage, tracker)
        assert result2 is None  # already migrated

    def test_parse_modules(self):
        content = "### Module 1: Intro\n### Module 2: Advanced\n### Module 3: Expert"
        assert _parse_modules(content) == ["Intro", "Advanced", "Expert"]

    def test_parse_modules_numbered_list(self):
        content = "1. First thing\n2. Second thing\n3. Third thing"
        assert _parse_modules(content) == ["First thing", "Second thing", "Third thing"]

    def test_parse_modules_empty(self):
        assert _parse_modules("") == []

    def test_completed_path_migration(self, tmp_path):
        lp_dir = tmp_path / "learning_paths"
        self._make_lp(lp_dir, "Python", ["Basics", "Advanced"], completed=2, status="completed")

        storage = MagicMock()
        storage.create.return_value = str(tmp_path / "goal.md")
        goal_file = tmp_path / "goal.md"
        post = frontmatter.Post("")
        post.metadata = {"title": "Python", "status": "active", "milestones": []}
        goal_file.write_text(frontmatter.dumps(post))

        tracker = GoalTracker(storage)
        result = migrate_learning_paths(tmp_path, storage, tracker)

        assert result["migrated"] == 1
        # Should have called update_goal_status to completed
        assert tracker.update_goal_status


# === Removal verification ===


class TestRemovals:
    def test_no_learning_router_in_app(self):
        """Verify learning router is not included in the app."""
        from web.app import app

        paths = [r.path for r in app.routes]
        assert not any("/api/learning" in str(p) for p in paths)

    def test_mcp_tool_count_decreased(self):
        """Verify learning tools removed from MCP server."""
        from coach_mcp.server import _load_tools

        registry = _load_tools()
        tool_names = [t.name for t in registry.get_mcp_definitions()]
        assert "learning_gaps" not in tool_names
        assert "learning_paths_list" not in tool_names
        assert "learning_path_get" not in tool_names
        assert "learning_path_progress" not in tool_names
        assert "learning_check_in" not in tool_names
