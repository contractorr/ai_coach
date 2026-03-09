"""Tests for briefing API routes."""

from types import SimpleNamespace
from unittest.mock import patch


def test_briefing_includes_daily_brief_and_feedback_count(client, auth_headers):
    data = {
        "recommendations": [
            {
                "id": "rec-1",
                "category": "projects",
                "title": "Ship MVP",
                "description": "Scope tightly",
                "score": 9.1,
                "status": "suggested",
                "reasoning_trace": None,
                "critic": None,
                "harvested_outcome": {
                    "state": "positive",
                    "confidence": 0.84,
                    "source_summary": "Completed action item and positive follow-through signals.",
                    "user_overridden": False,
                    "evidence": [],
                },
            }
        ],
        "stale_goals": [
            {"path": "goal-1.md", "title": "Learn Rust", "status": "active", "days_since_check": 12}
        ],
        "all_goals": [
            {"path": "goal-1.md", "title": "Learn Rust", "status": "active", "days_since_check": 12}
        ],
        "goal_intel_matches": [
            {
                "id": 1,
                "goal_path": "goal-1.md",
                "goal_title": "Learn Rust",
                "url": "https://example.com/rust",
                "title": "Rust update",
                "summary": "New release",
                "score": 0.8,
                "urgency": "medium",
                "match_reasons": ["matches goal"],
                "created_at": "2026-03-07T00:00:00",
                "llm_evaluated": False,
            }
        ],
        "dossier_escalations": [
            {
                "escalation_id": "esc-1",
                "topic_key": "acme-hiring",
                "topic_label": "Acme hiring",
                "score": 0.86,
                "state": "active",
                "evidence": {"thread_id": "thread-1"},
                "payload": {"topic": "Acme hiring"},
                "created_at": "2026-03-07T00:00:00",
                "updated_at": "2026-03-07T00:00:00",
                "snoozed_until": None,
                "dismissed_at": None,
                "accepted_dossier_id": None,
            }
        ],
        "company_movements": [
            {
                "id": 1,
                "company_key": "openai",
                "company_label": "OpenAI",
                "movement_type": "pricing",
                "title": "OpenAI pricing update",
                "summary": "Enterprise plan changed",
                "significance": 0.82,
                "source_url": "https://example.com/openai-pricing",
                "source_family": "rss",
                "observed_at": "2026-03-07T00:00:00",
                "metadata": {},
            }
        ],
        "hiring_signals": [
            {
                "id": 1,
                "entity_key": "openai",
                "entity_label": "OpenAI",
                "signal_type": "hiring_signal",
                "title": "Hiring signal at OpenAI",
                "summary": "Open roles expanded",
                "strength": 0.7,
                "source_url": "https://example.com/openai-hiring",
                "observed_at": "2026-03-07T00:00:00",
                "metadata": {},
            }
        ],
        "regulatory_alerts": [
            {
                "id": 1,
                "target_key": "ai-act",
                "title": "EU AI Act finalized",
                "summary": "New guidance landed",
                "source_family": "rss",
                "change_type": "finalized",
                "urgency": "high",
                "relevance": 0.88,
                "effective_date": None,
                "source_url": "https://example.com/ai-act",
                "observed_at": "2026-03-07T00:00:00",
                "metadata": {},
            }
        ],
        "assumptions": [
            {
                "id": "asm-1",
                "title": "Hiring stays strong for Acme",
                "detail": "Recent expansion supports this assumption.",
                "status": "confirmed",
                "updated_at": "2026-03-07T00:00:00",
            }
        ],
    }
    brief = SimpleNamespace(
        items=[
            SimpleNamespace(
                kind="stale_goal",
                title="Check in on Learn Rust",
                description="Goal has gone quiet",
                time_minutes=15,
                action="Open goal",
                priority=9,
            )
        ],
        budget_minutes=60,
        used_minutes=15,
        generated_at="2026-03-07T08:00:00",
    )

    with (
        patch("web.routes.briefing.assemble_briefing_data", return_value=data),
        patch("web.routes.briefing.get_feedback_count", return_value=4),
        patch("advisor.daily_brief.DailyBriefBuilder.build", return_value=brief),
    ):
        response = client.get("/api/briefing?max_recommendations=5", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["has_data"] is True
    assert body["adaptation_count"] == 4
    assert body["recommendations"][0]["title"] == "Ship MVP"
    assert body["recommendations"][0]["harvested_outcome"]["state"] == "positive"
    assert body["daily_brief"]["budget_minutes"] == 60
    assert body["daily_brief"]["items"][0]["title"] == "Check in on Learn Rust"
    assert body["goal_intel_matches"][0]["goal_title"] == "Learn Rust"
    assert body["dossier_escalations"][0]["topic_label"] == "Acme hiring"
    assert body["company_movements"][0]["company_label"] == "OpenAI"
    assert body["hiring_signals"][0]["entity_label"] == "OpenAI"
    assert body["regulatory_alerts"][0]["urgency"] == "high"
    assert body["assumptions"][0]["status"] == "confirmed"


def test_briefing_gracefully_skips_daily_brief_failures(client, auth_headers):
    data = {
        "recommendations": [],
        "stale_goals": [],
        "all_goals": [],
        "goal_intel_matches": [],
        "dossier_escalations": [],
        "company_movements": [],
        "hiring_signals": [],
        "regulatory_alerts": [],
        "assumptions": [],
    }

    with (
        patch("web.routes.briefing.assemble_briefing_data", return_value=data),
        patch("web.routes.briefing.get_feedback_count", side_effect=RuntimeError("feedback down")),
        patch(
            "advisor.daily_brief.DailyBriefBuilder.build", side_effect=RuntimeError("brief failed")
        ),
    ):
        response = client.get("/api/briefing", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "recommendations": [],
        "stale_goals": [],
        "goals": [],
        "has_data": False,
        "adaptation_count": 0,
        "daily_brief": None,
        "goal_intel_matches": [],
        "dossier_escalations": [],
        "company_movements": [],
        "hiring_signals": [],
        "regulatory_alerts": [],
        "assumptions": [],
    }
