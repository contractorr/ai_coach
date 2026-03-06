"""Daily brief MCP tool."""

from coach_mcp.bootstrap import get_components


def _get_daily_brief(args: dict) -> dict:
    """Build time-budgeted daily action plan."""
    from advisor.daily_brief import DailyBriefBuilder
    from advisor.goals import GoalTracker
    from advisor.recommendation_storage import RecommendationStorage
    from cli.utils import get_profile_storage, get_rec_db_path

    c = get_components()

    tracker = GoalTracker(c["storage"])
    stale_goals = tracker.get_stale_goals(days_threshold=7)
    all_goals = tracker.get_goals(include_inactive=False)

    recs = []
    try:
        rec_dir = get_rec_db_path(c["config"])
        if rec_dir.exists():
            recs = RecommendationStorage(rec_dir).get_top_by_score(limit=5)
    except Exception:
        pass

    weekly_hours = 5
    try:
        prof = get_profile_storage(c["config"]).load()
        if prof and hasattr(prof, "weekly_hours_available"):
            weekly_hours = prof.weekly_hours_available or 5
    except Exception:
        pass

    brief = DailyBriefBuilder().build(
        stale_goals=stale_goals,
        recommendations=recs,
        all_goals=all_goals,
        weekly_hours=weekly_hours,
    )

    return {
        "items": [
            {
                "kind": item.kind,
                "title": item.title,
                "description": item.description,
                "time_minutes": item.time_minutes,
                "action": item.action,
                "priority": item.priority,
            }
            for item in brief.items
        ],
        "budget_minutes": brief.budget_minutes,
        "used_minutes": brief.used_minutes,
        "generated_at": brief.generated_at,
    }


TOOLS = [
    (
        "get_daily_brief",
        {
            "description": "Get a time-budgeted daily action plan based on stale goals and recommendations. No LLM needed — pure structured data.",
            "type": "object",
            "properties": {},
            "required": [],
        },
        _get_daily_brief,
    ),
]
