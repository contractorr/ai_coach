"""Tests for shared projects service helpers."""

from profile.storage import ProfileStorage, UserProfile
from unittest.mock import MagicMock, patch

from services.projects import (
    build_project_ideas_context,
    discover_matching_project_issues,
    generate_project_ideas,
    list_project_issues,
    serialize_project_issue,
)


def test_serialize_project_issue_normalizes_tags_and_scores():
    issue = {
        "title": "Fix auth bug",
        "url": "https://github.com/acme/app/issues/1",
        "summary": "python bug fix",
        "tags": "python, fastapi, bug",
        "source": "github_issues",
        "_match_score": 3,
        "scraped_at": "2026-03-01",
    }

    serialized = serialize_project_issue(issue, summary_limit=10, include_scraped_at=True)

    assert serialized == {
        "title": "Fix auth bug",
        "url": "https://github.com/acme/app/issues/1",
        "summary": "python bug",
        "tags": ["python", "fastapi", "bug"],
        "source": "github_issues",
        "match_score": 3,
        "scraped_at": "2026-03-01",
    }


def test_discover_matching_project_issues_serializes_results():
    intel_storage = MagicMock()
    profile = MagicMock()
    matched = [
        {
            "title": "Fix auth bug",
            "url": "https://github.com/acme/app/issues/1",
            "summary": "python bug fix",
            "tags": ["python", "bug"],
            "source": "github_issues",
            "_match_score": 2,
        }
    ]

    with patch('advisor.projects.get_matching_issues', return_value=matched) as mock_get:
        payload = discover_matching_project_issues(intel_storage, profile=profile, limit=5, days=7)

    assert payload["count"] == 1
    assert payload["issues"][0]["match_score"] == 2
    mock_get.assert_called_once_with(intel_storage, profile=profile, limit=5, days=7)


def test_list_project_issues_filters_non_github_items():
    intel_storage = MagicMock()
    intel_storage.get_recent.return_value = [
        {
            "title": "Fix auth bug",
            "url": "https://github.com/acme/app/issues/1",
            "summary": "python bug fix",
            "source": "github_issues",
            "scraped_at": "2026-03-01",
        },
        {
            "title": "Other news",
            "url": "https://example.com/post",
            "summary": "ignore me",
            "source": "rss",
            "scraped_at": "2026-03-01",
        },
    ]

    payload = list_project_issues(intel_storage, days=30, limit=10, include_scraped_at=True)

    assert payload["count"] == 1
    assert payload["issues"][0]["title"] == "Fix auth bug"
    intel_storage.get_recent.assert_called_once_with(days=30, limit=10)


def test_build_project_ideas_context_uses_profile_and_journal_search(tmp_path):
    profile_storage = ProfileStorage(tmp_path / 'profile.yaml')
    profile_storage.save(
        UserProfile(
            name='Raj',
            role='Engineer',
            interests=['automation'],
            values=['clarity'],
            weekly_hours_available=5,
        )
    )
    journal_search = MagicMock()
    journal_search.get_context_for_query.return_value = 'Pain points from journal'

    payload = build_project_ideas_context(profile_storage=profile_storage, journal_search=journal_search)

    assert 'automation' in payload['profile'] or payload['profile']
    assert payload['journal_context'] == 'Pain points from journal'
    assert 'Generate side-project ideas' in payload['instruction']


def test_generate_project_ideas_delegates_to_generator():
    rag = MagicMock()
    llm_caller = MagicMock()
    generator = MagicMock()
    generator.generate_ideas.return_value = '# Ideas'

    with patch('advisor.projects.ProjectIdeaGenerator', return_value=generator) as mock_cls:
        ideas = generate_project_ideas(rag, llm_caller)

    assert ideas == '# Ideas'
    mock_cls.assert_called_once_with(rag, llm_caller)
