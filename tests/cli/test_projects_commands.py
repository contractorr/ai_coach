"""Tests for project discovery CLI delegation."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_projects_discover_uses_shared_service(runner):
    components = {
        "intel_storage": MagicMock(),
        "config": {"profile": {}},
    }
    profile_storage = MagicMock()
    profile_storage.load.return_value = MagicMock()

    with (
        patch("cli.commands.projects.get_components", return_value=components),
        patch("cli.commands.projects.get_profile_storage", return_value=profile_storage),
        patch(
            "cli.commands.projects.discover_matching_project_issues",
            return_value={
                "issues": [
                    {
                        "title": "Fix auth bug",
                        "summary": "Repo: acme/app | FastAPI auth cleanup",
                        "tags": ["python", "fastapi"],
                        "match_score": 2,
                    }
                ],
                "count": 1,
            },
        ) as mock_discover,
    ):
        result = runner.invoke(cli, ["projects", "discover", "--limit", "5", "--days", "7"])

    assert result.exit_code == 0
    assert "Fix auth bug" in result.output
    mock_discover.assert_called_once_with(
        components["intel_storage"], profile=profile_storage.load.return_value, limit=5, days=7
    )


def test_projects_ideas_uses_shared_generator(runner):
    components = {
        "rag": MagicMock(),
        "advisor": MagicMock(_call_llm=MagicMock()),
    }

    with (
        patch("cli.commands.projects.get_components", return_value=components),
        patch(
            "cli.commands.projects.generate_project_ideas", return_value="# Ideas"
        ) as mock_generate,
    ):
        result = runner.invoke(cli, ["projects", "ideas"])

    assert result.exit_code == 0
    assert "Ideas" in result.output
    mock_generate.assert_called_once_with(components["rag"], components["advisor"]._call_llm)


def test_projects_list_uses_shared_list_service(runner):
    components = {"intel_storage": MagicMock()}

    with (
        patch("cli.commands.projects.get_components", return_value=components),
        patch(
            "cli.commands.projects.list_project_issues",
            return_value={
                "issues": [
                    {
                        "title": "Fix auth bug",
                        "summary": "Short summary",
                        "url": "https://github.com/acme/app/issues/1",
                    }
                ],
                "count": 1,
            },
        ) as mock_list,
    ):
        result = runner.invoke(cli, ["projects", "list", "--days", "21"])

    assert result.exit_code == 0
    assert "Fix auth bug" in result.output
    mock_list.assert_called_once_with(components["intel_storage"], days=21, limit=50)
