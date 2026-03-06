"""Unified Suggestions endpoint — merges recommendations + daily brief items."""

from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, Query

from web.auth import get_current_user
from web.briefing_data import assemble_briefing_data
from web.deps import get_user_paths
from web.models import SuggestionItem

logger = structlog.get_logger()

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])


@router.get("", response_model=list[SuggestionItem])
async def get_suggestions(
    limit: int = Query(default=10, ge=1, le=30),
    user: dict = Depends(get_current_user),
):
    """Return a unified list of suggestions combining daily brief items and recommendations."""
    data = assemble_briefing_data(user["id"])
    paths = get_user_paths(user["id"])

    suggestions: list[SuggestionItem] = []

    # Build daily brief items as high-priority suggestions
    try:
        from profile.storage import ProfileStorage

        from advisor.daily_brief import DailyBriefBuilder

        weekly_hours = 5
        profile_path = paths.get("profile")
        if profile_path and Path(profile_path).exists():
            prof = ProfileStorage(profile_path).load()
            if prof and hasattr(prof, "weekly_hours_available"):
                weekly_hours = prof.weekly_hours_available or 5

        brief = DailyBriefBuilder().build(
            stale_goals=data["stale_goals"],
            recommendations=data["recommendations"],
            all_goals=data["all_goals"],
            weekly_hours=weekly_hours,
            intel_matches=data["goal_intel_matches"],
        )
        for item in brief.items:
            suggestions.append(
                SuggestionItem(
                    source="brief",
                    kind=item.kind,
                    title=item.title,
                    description=item.description,
                    action=item.action,
                    priority=item.priority,
                    score=0.0,
                )
            )
    except Exception as e:
        logger.warning("suggestions.brief_error", error=str(e))

    # Add remaining recommendations not already in brief
    brief_titles = {s.title for s in suggestions if s.source == "brief"}
    for rec in data["recommendations"]:
        if rec["title"] in brief_titles:
            continue
        suggestions.append(
            SuggestionItem(
                source="recommendation",
                kind="recommendation",
                title=rec["title"],
                description=rec.get("description", ""),
                action=f"Tell me more about: {rec['title']}",
                priority=0,
                score=rec.get("score", 0.0),
            )
        )

    return suggestions[:limit]
