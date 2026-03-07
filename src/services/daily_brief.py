"""Shared daily-brief orchestration for web, CLI, and MCP surfaces."""

from typing import Any

from advisor.daily_brief import DailyBrief, DailyBriefBuilder

DEFAULT_WEEKLY_HOURS = 5


def _item_value(item: Any, key: str, default: Any = None) -> Any:
    """Read a brief-item field from either an object or dict."""
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def resolve_weekly_hours(profile: Any, default_hours: int = DEFAULT_WEEKLY_HOURS) -> int:
    """Resolve a user's weekly-hours budget from a loaded profile."""
    if profile is None:
        return default_hours

    weekly_hours = getattr(profile, "weekly_hours_available", None)
    return weekly_hours or default_hours


def load_weekly_hours(profile_storage, default_hours: int = DEFAULT_WEEKLY_HOURS) -> int:
    """Load a profile and resolve weekly-hours budget with a safe default."""
    if profile_storage is None:
        return default_hours

    try:
        profile = profile_storage.load()
    except Exception:
        return default_hours
    return resolve_weekly_hours(profile, default_hours=default_hours)


def collect_daily_brief_inputs(
    journal_storage,
    *,
    profile_storage=None,
    recommendation_storage=None,
    stale_days: int = 7,
    recommendation_limit: int = 5,
) -> dict[str, Any]:
    """Collect reusable daily-brief inputs from shared storage objects."""
    from advisor.goals import GoalTracker

    tracker = GoalTracker(journal_storage)
    stale_goals = tracker.get_stale_goals(days_threshold=stale_days)
    all_goals = tracker.get_goals(include_inactive=False)

    recommendations = []
    if recommendation_storage is not None:
        try:
            recommendations = recommendation_storage.get_top_by_score(limit=recommendation_limit)
        except Exception:
            recommendations = []

    return {
        "stale_goals": stale_goals,
        "recommendations": recommendations,
        "all_goals": all_goals,
        "weekly_hours": load_weekly_hours(profile_storage),
    }


def build_daily_brief(
    *,
    stale_goals: list[dict],
    recommendations: list[Any],
    all_goals: list[dict],
    weekly_hours: int = DEFAULT_WEEKLY_HOURS,
    goal_intel_matches: list[dict] | None = None,
) -> DailyBrief:
    """Build the daily brief from pre-assembled inputs."""
    return DailyBriefBuilder().build(
        stale_goals=stale_goals,
        recommendations=recommendations,
        all_goals=all_goals,
        weekly_hours=weekly_hours,
        intel_matches=goal_intel_matches,
    )


def serialize_daily_brief(brief: DailyBrief) -> dict[str, Any]:
    """Serialize a daily brief into DTO-style primitives for surfaces."""
    return {
        "items": [
            {
                "kind": _item_value(item, "kind", ""),
                "title": _item_value(item, "title", ""),
                "description": _item_value(item, "description", ""),
                "time_minutes": _item_value(item, "time_minutes", 0),
                "action": _item_value(item, "action", ""),
                "priority": _item_value(item, "priority", 0),
            }
            for item in brief.items
        ],
        "budget_minutes": _item_value(brief, "budget_minutes", 0),
        "used_minutes": _item_value(brief, "used_minutes", 0),
        "generated_at": _item_value(brief, "generated_at", ""),
    }


def build_daily_brief_payload(
    *,
    stale_goals: list[dict],
    recommendations: list[Any],
    all_goals: list[dict],
    weekly_hours: int = DEFAULT_WEEKLY_HOURS,
    goal_intel_matches: list[dict] | None = None,
) -> dict[str, Any]:
    """Build and serialize a daily brief for surface-friendly responses."""
    brief = build_daily_brief(
        stale_goals=stale_goals,
        recommendations=recommendations,
        all_goals=all_goals,
        weekly_hours=weekly_hours,
        goal_intel_matches=goal_intel_matches,
    )
    return serialize_daily_brief(brief)
