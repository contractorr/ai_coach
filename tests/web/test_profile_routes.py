"""Tests for profile API routes."""

from unittest.mock import patch


def test_get_empty_profile_returns_defaults(client, auth_headers):
    response = client.get("/api/profile", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["current_role"] == ""
    assert response.json()["skills"] == []
    assert response.json()["summary"] == ""
    assert response.json()["weekly_hours_available"] == 5


def test_patch_profile_persists_and_returns_summary(client, auth_headers):
    payload = {
        "current_role": "Backend Engineer",
        "career_stage": "senior",
        "skills": [{"name": "Python", "proficiency": 5}],
        "languages_frameworks": ["FastAPI", "Postgres"],
        "goals_short_term": "Ship a reliable API",
        "active_projects": ["StewardMe"],
    }

    with patch("web.routes.profile._embed_profile"):
        patch_response = client.patch("/api/profile", headers=auth_headers, json=payload)

    assert patch_response.status_code == 200
    assert patch_response.json() == {
        "ok": True,
        "updated_fields": [
            "current_role",
            "career_stage",
            "skills",
            "languages_frameworks",
            "goals_short_term",
            "active_projects",
        ],
    }

    get_response = client.get("/api/profile", headers=auth_headers)
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["current_role"] == "Backend Engineer"
    assert data["career_stage"] == "senior"
    assert data["skills"] == [{"name": "Python", "proficiency": 5}]
    assert data["languages_frameworks"] == ["FastAPI", "Postgres"]
    assert data["goals_short_term"] == "Ship a reliable API"
    assert data["active_projects"] == ["StewardMe"]
    assert data["summary"]
    assert data["is_stale"] is False
    assert data["updated_at"]


def test_patch_profile_requires_fields(client, auth_headers):
    response = client.patch("/api/profile", headers=auth_headers, json={})

    assert response.status_code == 400
    assert response.json() == {"detail": "No fields to update"}
