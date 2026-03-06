"""CLI command tests using Click CliRunner.

Strategy: mock get_components at each command module's import point to avoid
touching real config/DB/API. Each test patches exactly what it needs.
"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli.commands.journal import resolve_journal_path
from cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


def _make_components(tmp_path, skip_advisor=False):
    """Build a fake components dict matching cli.utils.get_components return."""
    mock_storage = MagicMock()
    mock_storage.create.return_value = tmp_path / "journal" / "test.md"
    mock_storage.list_entries.return_value = [
        {
            "created": "2024-01-01T10:00:00",
            "type": "daily",
            "title": "Day 1",
            "tags": ["test"],
            "path": tmp_path / "journal" / "test.md",
        }
    ]
    post_mock = MagicMock(content="Test body")
    post_mock.get = lambda k, d=None: {
        "title": "Day 1",
        "type": "daily",
        "created": "2024-01-01",
    }.get(k, d)
    mock_storage.read.return_value = post_mock

    mock_advisor = MagicMock()
    mock_advisor.ask.return_value = "AI response text"
    mock_advisor.weekly_review.return_value = "Review text"
    mock_advisor.detect_opportunities.return_value = "Opportunities text"
    mock_advisor.analyze_goals.return_value = "Goals analysis"
    mock_advisor.generate_recommendations.return_value = []
    mock_advisor.generate_action_brief.return_value = "# Brief"

    return {
        "storage": mock_storage,
        "embeddings": MagicMock(count=MagicMock(return_value=5)),
        "search": MagicMock(
            sync_embeddings=MagicMock(return_value=(2, 0)),
            semantic_search=MagicMock(return_value=[]),
        ),
        "intel_storage": MagicMock(
            get_recent=MagicMock(
                return_value=[
                    {
                        "title": "HN Story",
                        "source": "hackernews",
                        "scraped_at": "2024-01-01T00:00:00",
                        "summary": "A story",
                        "url": "https://example.com",
                    }
                ]
            )
        ),
        "intel_search": MagicMock(),
        "advisor": None if skip_advisor else mock_advisor,
        "config": {
            "sources": {"enabled": ["hn_top"], "rss_feeds": [], "custom_blogs": []},
            "recommendations": {},
            "research": {"enabled": False},
            "paths": {"intel_db": str(tmp_path / "intel.db")},
            "llm": {"model": "claude-sonnet-4-6"},
        },
        "config_model": MagicMock(),
        "paths": {
            "journal_dir": tmp_path / "journal",
            "chroma_dir": tmp_path / "chroma",
            "intel_db": tmp_path / "intel.db",
        },
        "rag": MagicMock(),
    }


@pytest.fixture
def patch_components(tmp_path):
    """Patch get_components everywhere it's imported."""
    comps = _make_components(tmp_path)

    def fake_get_components(skip_advisor=False):
        c = dict(comps)
        if skip_advisor:
            c["advisor"] = None
        return c

    targets = [
        "cli.commands.journal.get_components",
        "cli.commands.advisor.get_components",
        "cli.commands.intelligence.get_components",
        "cli.commands.research.get_components",
        "cli.commands.recommend.get_components",
        "cli.commands.trends.get_components",
        "cli.commands.daemon.get_components",
    ]
    patches = [patch(t, side_effect=fake_get_components) for t in targets]
    for p in patches:
        p.start()
    yield comps
    for p in patches:
        p.stop()


# -- Journal commands --


class TestJournalCommands:
    def test_add(self, runner, patch_components):
        result = runner.invoke(cli, ["journal", "add", "Test content"])
        assert result.exit_code == 0
        assert "Created" in result.output

    def test_list(self, runner, patch_components):
        result = runner.invoke(cli, ["journal", "list"])
        assert result.exit_code == 0

    def test_export_json(self, runner, patch_components, tmp_path):
        out = tmp_path / "out.json"
        with patch("journal.export.JournalExporter") as cls:
            cls.return_value.export_json.return_value = 3
            result = runner.invoke(cli, ["journal", "export", "-o", str(out), "-f", "json"])
        assert result.exit_code == 0
        assert "Exported" in result.output


# -- Advisor commands --


class TestAdvisorCommands:
    def test_ask(self, runner, patch_components):
        result = runner.invoke(cli, ["ask", "What should I learn?"])
        assert result.exit_code == 0

    def test_review(self, runner, patch_components):
        result = runner.invoke(cli, ["review"])
        assert result.exit_code == 0

    def test_opportunities(self, runner, patch_components):
        result = runner.invoke(cli, ["opportunities"])
        assert result.exit_code == 0


# -- Intelligence commands --


class TestIntelCommands:
    def test_scrape(self, runner, patch_components):
        with patch("cli.commands.intelligence.IntelScheduler") as cls:
            cls.return_value.run_now.return_value = {"hackernews": {"scraped": 10, "new": 5}}
            result = runner.invoke(cli, ["scrape"])
        assert result.exit_code == 0

    def test_brief(self, runner, patch_components):
        result = runner.invoke(cli, ["brief"])
        assert result.exit_code == 0

    def test_sources(self, runner, patch_components):
        result = runner.invoke(cli, ["sources"])
        assert result.exit_code == 0

    def test_watchlist_add_list_remove(self, runner, patch_components):
        add_result = runner.invoke(
            cli,
            ["watchlist", "add", "OpenAI", "--priority", "high", "--why", "Career relevance"],
        )
        assert add_result.exit_code == 0
        assert "Saved" in add_result.output

        list_result = runner.invoke(cli, ["watchlist", "list"])
        assert list_result.exit_code == 0
        assert "OpenAI" in list_result.output

        item_id = add_result.output.strip().split("(")[-1].rstrip(")")
        remove_result = runner.invoke(cli, ["watchlist", "remove", item_id])
        assert remove_result.exit_code == 0
        assert "Removed" in remove_result.output


# -- Goals command --


class TestGoalsCommands:
    def test_add(self, runner, patch_components):
        result = runner.invoke(
            cli, ["goals", "add", "-t", "Learn Rust", "-d", "Systems programming"]
        )
        assert result.exit_code == 0


class TestRecommendActionCommands:
    def test_action_create(self, runner, patch_components, tmp_path):
        with patch("cli.commands.recommend.RecommendationStorage") as cls:
            storage = cls.return_value
            storage.create_action_item.return_value = {"status": "accepted"}
            storage.get_action_item.return_value = MagicMock(
                recommendation_title="Ship MVP",
                category="projects",
                action_item={
                    "status": "accepted",
                    "effort": "medium",
                    "due_window": "this_week",
                    "objective": "Ship MVP",
                    "next_step": "Outline scope",
                    "success_criteria": "Working prototype",
                },
            )
            result = runner.invoke(cli, ["recommend", "action", "create", "abc123"])
        assert result.exit_code == 0
        assert "Tracked action created" in result.output

    def test_action_list(self, runner, patch_components):
        with patch("cli.commands.recommend.RecommendationStorage") as cls:
            storage = cls.return_value
            storage.list_action_items.return_value = [
                MagicMock(
                    recommendation_id="abc123",
                    recommendation_title="Ship MVP",
                    action_item={
                        "status": "accepted",
                        "effort": "medium",
                        "due_window": "this_week",
                        "goal_title": "Launch side project",
                    },
                )
            ]
            result = runner.invoke(cli, ["recommend", "action", "list"])
        assert result.exit_code == 0
        assert "Ship MVP" in result.output

    def test_action_update(self, runner, patch_components):
        with patch("cli.commands.recommend.RecommendationStorage") as cls:
            storage = cls.return_value
            storage.update_action_item.return_value = {"status": "completed"}
            storage.get_action_item.return_value = MagicMock(
                recommendation_title="Ship MVP",
                category="projects",
                action_item={
                    "status": "completed",
                    "effort": "medium",
                    "due_window": "this_week",
                    "objective": "Ship MVP",
                    "next_step": "Ship it",
                    "success_criteria": "Working prototype",
                    "review_notes": "Done",
                },
            )
            result = runner.invoke(
                cli,
                ["recommend", "action", "update", "abc123", "--status", "completed"],
            )
        assert result.exit_code == 0
        assert "Updated tracked action" in result.output

    def test_action_weekly_plan(self, runner, patch_components):
        with patch("cli.commands.recommend.RecommendationStorage") as cls:
            storage = cls.return_value
            storage.build_weekly_plan.return_value = {
                "capacity_points": 6,
                "used_points": 2,
                "items": [
                    MagicMock(
                        recommendation_title="Ship MVP",
                        category="projects",
                        action_item={
                            "status": "accepted",
                            "effort": "medium",
                            "due_window": "this_week",
                            "objective": "Ship MVP",
                            "next_step": "Outline scope",
                            "success_criteria": "Working prototype",
                        },
                    )
                ],
            }
            result = runner.invoke(cli, ["recommend", "action", "weekly-plan"])
        assert result.exit_code == 0
        assert "Weekly plan" in result.output

    def test_list(self, runner, patch_components):
        with patch("advisor.goals.GoalTracker") as cls:
            cls.return_value.get_goals.return_value = [
                {
                    "path": "/g.md",
                    "title": "Learn Rust",
                    "status": "active",
                    "last_checked": "2024-01-01",
                    "days_since_check": 3,
                    "is_stale": False,
                }
            ]
            result = runner.invoke(cli, ["goals", "list"])
        assert result.exit_code == 0


# -- Init command --


class TestPathValidation:
    def test_resolve_normal_path(self, tmp_path):
        journal_dir = tmp_path / "journal"
        journal_dir.mkdir()
        (journal_dir / "entry.md").write_text("hello")
        result = resolve_journal_path(journal_dir, "entry.md")
        assert result is not None
        assert result.name == "entry.md"

    def test_resolve_traversal_blocked(self, tmp_path):
        journal_dir = tmp_path / "journal"
        journal_dir.mkdir()
        result = resolve_journal_path(journal_dir, "../../etc/passwd")
        assert result is None

    def test_resolve_partial_match(self, tmp_path):
        journal_dir = tmp_path / "journal"
        journal_dir.mkdir()
        (journal_dir / "2024-01-01_daily_day-1.md").write_text("hello")
        result = resolve_journal_path(journal_dir, "day-1")
        assert result is not None
        assert "day-1" in result.name

    def test_resolve_nonexistent(self, tmp_path):
        journal_dir = tmp_path / "journal"
        journal_dir.mkdir()
        result = resolve_journal_path(journal_dir, "nope.md")
        assert result is None


class TestInitCommand:
    def test_init(self, runner, tmp_path):
        with (
            patch("cli.commands.init.load_config") as mock_cfg,
            patch("cli.commands.init.get_paths") as mock_paths,
        ):
            mock_cfg.return_value = {}
            mock_paths.return_value = {
                "journal_dir": tmp_path / "j",
                "chroma_dir": tmp_path / "c",
                "intel_db": tmp_path / "i.db",
            }
            result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "Minimal setup" in result.output
