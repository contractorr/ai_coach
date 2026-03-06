"""Daily briefing routes — aggregates recommendations, stale goals, daily brief."""

from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, Query

from web.auth import get_current_user
from web.briefing_data import assemble_briefing_data
from web.deps import get_user_paths
from web.models import (
    BriefingGoal,
    BriefingRecommendation,
    BriefingResponse,
    GoalIntelMatch,
)
from web.models import (
    DailyBrief as DailyBriefModel,
)
from web.models import (
    DailyBriefItem as DailyBriefItemModel,
)
from web.user_store import get_feedback_count

logger = structlog.get_logger()

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("", response_model=BriefingResponse)
async def get_briefing(
    max_recommendations: int = Query(default=5, ge=1, le=20),
    user: dict = Depends(get_current_user),
):
    # Shared data assembly
    data = assemble_briefing_data(user["id"])
    paths = get_user_paths(user["id"])

    recommendations = data["recommendations"][:max_recommendations]
    stale_goals = data["stale_goals"]
    all_goals = data["all_goals"]
    goal_intel_matches = data["goal_intel_matches"]

    has_data = bool(recommendations or stale_goals or all_goals or goal_intel_matches)

    # Adaptation count
    adaptation_count = 0
    try:
        adaptation_count = get_feedback_count(user["id"])
    except Exception:
        pass

    # Daily brief
    daily_brief = None
    try:
        from profile.storage import ProfileStorage

        from advisor.daily_brief import DailyBriefBuilder

        weekly_hours = 5
        profile_path = paths.get("profile")
        if profile_path and Path(profile_path).exists():
            prof = ProfileStorage(profile_path).load()
            if prof and hasattr(prof, "weekly_hours_available"):
                weekly_hours = prof.weekly_hours_available or 5

        brief_data = DailyBriefBuilder().build(
            stale_goals=stale_goals,
            recommendations=recommendations,
            all_goals=all_goals,
            weekly_hours=weekly_hours,
            intel_matches=goal_intel_matches,
        )
        daily_brief = DailyBriefModel(
            items=[
                DailyBriefItemModel(
                    kind=item.kind,
                    title=item.title,
                    description=item.description,
                    time_minutes=item.time_minutes,
                    action=item.action,
                    priority=item.priority,
                )
                for item in brief_data.items
            ],
            budget_minutes=brief_data.budget_minutes,
            used_minutes=brief_data.used_minutes,
            generated_at=brief_data.generated_at,
        )
    except Exception as e:
        logger.warning("briefing.daily_brief_error", error=str(e))

    return BriefingResponse(
        recommendations=[BriefingRecommendation(**r) for r in recommendations],
        stale_goals=[BriefingGoal(**g) for g in stale_goals],
        goals=[BriefingGoal(**g) for g in all_goals],
        has_data=has_data,
        adaptation_count=adaptation_count,
        daily_brief=daily_brief,
        goal_intel_matches=[GoalIntelMatch(**m) for m in goal_intel_matches],
    )
