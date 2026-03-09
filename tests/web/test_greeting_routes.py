"""Tests for greeting API routes."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from advisor.greeting import STATIC_FALLBACK


def test_greeting_returns_fallback_when_no_cache(client, auth_headers, tmp_path):
    """First call returns static fallback with stale=True."""
    with patch("web.routes.greeting._get_cache") as mock_cache:
        cache = MagicMock()
        cache.get.return_value = None  # no cached greeting
        mock_cache.return_value = cache

        res = client.get("/api/greeting", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert data["text"] == STATIC_FALLBACK
    assert data["cached"] is False
    assert data["stale"] is True


def test_greeting_returns_cached(client, auth_headers, tmp_path):
    """When cache has a greeting, return it with cached=True."""
    with patch("web.routes.greeting._get_cache") as mock_cache:
        cache = MagicMock()
        cache.get.return_value = None
        mock_cache.return_value = cache

        with patch("web.routes.greeting.get_cached_greeting", return_value="Hello from cache"):
            res = client.get("/api/greeting", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert data["text"] == "Hello from cache"
    assert data["cached"] is True
    assert data["stale"] is False


def test_greeting_unauthenticated(client):
    """No token = 401."""
    res = client.get("/api/greeting")
    assert res.status_code in (401, 403)


def test_greeting_return_brief_can_include_assumption_updates(client, auth_headers):
    with patch("web.routes.greeting._get_cache") as mock_cache:
        cache = MagicMock()
        cache.get.return_value = None
        mock_cache.return_value = cache

        with (
            patch("web.routes.greeting.get_cached_greeting", return_value=None),
            patch(
                "web.routes.greeting.assemble_briefing_data",
                return_value={
                    "name": "",
                    "stale_goals": [],
                    "all_goals": [],
                    "recommendations": [],
                    "goal_intel_matches": [],
                    "company_movements": [
                        {
                            "title": "OpenAI pricing update",
                            "summary": "Enterprise plan changed",
                            "company_label": "OpenAI",
                        }
                    ],
                    "hiring_signals": [],
                    "regulatory_alerts": [
                        {
                            "title": "EU AI Act finalized",
                            "summary": "Guidance changed",
                            "urgency": "high",
                        }
                    ],
                    "assumptions": [
                        {
                            "title": "Hiring stays strong for Acme",
                            "detail": "Recent expansion supports this assumption.",
                            "status": "confirmed",
                        }
                    ],
                },
            ),
            patch(
                "web.routes.greeting.load_dossier_escalation_context",
                return_value={
                    "threads": [],
                    "recent_intel": [],
                    "watchlist": [],
                    "goals": [],
                    "dossiers": [],
                },
            ),
            patch(
                "web.routes.greeting.ReturnBriefBuilder.get_last_active_at",
                return_value=datetime.now() - timedelta(hours=96),
            ),
        ):
            res = client.get("/api/greeting", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert data["return_brief"] is not None
    assumption_sections = [
        section for section in data["return_brief"]["sections"] if section["kind"] == "assumptions"
    ]
    company_sections = [
        section
        for section in data["return_brief"]["sections"]
        if section["kind"] == "company_movements"
    ]
    regulatory_sections = [
        section
        for section in data["return_brief"]["sections"]
        if section["kind"] == "regulatory_alerts"
    ]
    assert len(assumption_sections) == 1
    assert assumption_sections[0]["items"][0]["title"] == "Hiring stays strong for Acme"
    assert len(company_sections) == 1
    assert company_sections[0]["items"][0]["title"] == "OpenAI pricing update"
    assert len(regulatory_sections) == 1
    assert regulatory_sections[0]["items"][0]["title"] == "EU AI Act finalized"


def test_greeting_return_brief_can_include_dossier_escalation_updates(client, auth_headers):
    with patch("web.routes.greeting._get_cache") as mock_cache:
        cache = MagicMock()
        cache.get.return_value = None
        mock_cache.return_value = cache

        with (
            patch("web.routes.greeting.get_cached_greeting", return_value=None),
            patch(
                "web.routes.greeting.assemble_briefing_data",
                return_value={
                    "name": "",
                    "stale_goals": [],
                    "all_goals": [],
                    "recommendations": [],
                    "goal_intel_matches": [],
                    "company_movements": [],
                    "hiring_signals": [],
                    "regulatory_alerts": [],
                    "assumptions": [],
                },
            ),
            patch(
                "web.routes.greeting.load_dossier_escalation_context",
                return_value={
                    "threads": [{"label": "Acme hiring", "entry_count": 6, "id": "thread-1"}],
                    "recent_intel": [
                        {"title": "Acme hiring expands", "summary": "More roles added"}
                    ],
                    "watchlist": [],
                    "goals": [],
                    "dossiers": [],
                },
            ),
            patch(
                "web.routes.greeting.ReturnBriefBuilder.get_last_active_at",
                return_value=datetime.now() - timedelta(hours=96),
            ),
        ):
            res = client.get("/api/greeting", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert data["return_brief"] is not None
    dossier_sections = [
        section for section in data["return_brief"]["sections"] if section["kind"] == "dossiers"
    ]
    assert len(dossier_sections) == 1
    assert dossier_sections[0]["items"][0]["title"] == "Acme hiring"
