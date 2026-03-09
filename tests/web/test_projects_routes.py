"""Tests for projects API routes."""

from unittest.mock import patch


def test_get_issues_returns_normalized_matches(client, auth_headers):
    mocked_results = [
        {
            "title": "Improve auth middleware",
            "url": "https://github.com/acme/app/issues/1",
            "summary": "FastAPI auth cleanup",
            "tags": "python,fastapi,security",
            "source": "github_issues",
            "_match_score": 3,
        },
        {
            "title": "Document CLI flags",
            "url": "https://github.com/acme/app/issues/2",
            "summary": "Improve contributor docs",
            "tags": ["docs", "cli"],
            "source": "github_issues",
            "_match_score": 1,
        },
    ]

    with patch("advisor.projects.get_matching_issues", return_value=mocked_results):
        response = client.get("/api/projects/issues?limit=5&days=7", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == [
        {
            "title": "Improve auth middleware",
            "url": "https://github.com/acme/app/issues/1",
            "summary": "FastAPI auth cleanup",
            "tags": ["python", "fastapi", "security"],
            "source": "github_issues",
            "match_score": 3,
        },
        {
            "title": "Document CLI flags",
            "url": "https://github.com/acme/app/issues/2",
            "summary": "Improve contributor docs",
            "tags": ["docs", "cli"],
            "source": "github_issues",
            "match_score": 1,
        },
    ]


def test_generate_ideas_requires_api_key(client, auth_headers):
    with patch("web.routes.projects.get_api_key_for_user", return_value=None):
        response = client.post("/api/projects/ideas", headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {"detail": "No LLM API key configured"}
