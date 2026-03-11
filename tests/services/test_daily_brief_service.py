"""Tests for shared daily-brief service helpers."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from services.daily_brief import (
    build_daily_brief_payload,
    collect_daily_brief_inputs,
    load_weekly_hours,
    resolve_weekly_hours,
)


def test_resolve_weekly_hours_uses_profile_value_or_default():
    assert resolve_weekly_hours(SimpleNamespace(weekly_hours_available=9)) == 9
    assert resolve_weekly_hours(SimpleNamespace(weekly_hours_available=0)) == 0
    assert resolve_weekly_hours(SimpleNamespace(weekly_hours_available=-3)) == 0
    assert resolve_weekly_hours(SimpleNamespace(weekly_hours_available=None)) == 5
    assert resolve_weekly_hours(None) == 5


def test_load_weekly_hours_handles_storage_failures():
    storage = MagicMock()
    storage.load.side_effect = RuntimeError("boom")

    assert load_weekly_hours(storage) == 5


def test_collect_daily_brief_inputs_assembles_shared_data():
    journal_storage = MagicMock()
    profile_storage = MagicMock()
    recommendation_storage = MagicMock()

    profile_storage.load.return_value = SimpleNamespace(weekly_hours_available=7)
    recommendation_storage.get_top_by_score.return_value = [
        SimpleNamespace(title="Learn Rust", description="Build a CLI")
    ]

    inputs = collect_daily_brief_inputs(
        journal_storage,
        profile_storage=profile_storage,
        recommendation_storage=recommendation_storage,
    )

    assert inputs["weekly_hours"] == 7
    assert isinstance(inputs["stale_goals"], list)
    assert isinstance(inputs["all_goals"], list)
    assert len(inputs["recommendations"]) == 1
    recommendation_storage.get_top_by_score.assert_called_once_with(limit=5)


def test_build_daily_brief_payload_serializes_surface_friendly_shape():
    payload = build_daily_brief_payload(
        stale_goals=[{"title": "Check in", "days_since_check": 10}],
        recommendations=[{"title": "Explore Go", "description": "Ship something small"}],
        all_goals=[{"title": "Check in"}],
        weekly_hours=5,
        goal_intel_matches=[
            {
                "title": "AI infra release",
                "summary": "Worth reviewing",
                "urgency": "high",
                "score": 0.4,
            }
        ],
    )

    assert payload["budget_minutes"] > 0
    assert payload["used_minutes"] > 0
    assert payload["generated_at"]
    assert payload["items"]
    assert set(payload["items"][0]) == {
        "kind",
        "title",
        "description",
        "time_minutes",
        "action",
        "priority",
    }


def test_build_daily_brief_payload_respects_zero_budget():
    payload = build_daily_brief_payload(
        stale_goals=[{"title": "Check in", "days_since_check": 10}],
        recommendations=[{"title": "Explore Go", "description": "Ship something small"}],
        all_goals=[{"title": "Check in"}],
        weekly_hours=0,
    )

    assert payload["budget_minutes"] == 0
    assert payload["used_minutes"] == 0
    assert payload["items"] == []
