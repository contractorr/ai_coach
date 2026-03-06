"""Daily briefing routes — aggregates recommendations, stale goals, daily brief."""

from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, Query

from advisor.goals import GoalTracker
from advisor.recommendation_storage import RecommendationStorage
from journal.storage import JournalStorage
from web.auth import get_current_user
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


def _get_storage(user_id: str) -> JournalStorage:
    paths = get_user_paths(user_id)
    return JournalStorage(paths["journal_dir"])


@router.get("", response_model=BriefingResponse)
async def get_briefing(
    max_recommendations: int = Query(default=5, ge=1, le=20),
    user: dict = Depends(get_current_user),
):
    paths = get_user_paths(user["id"])
    storage = _get_storage(user["id"])

    # Recommendations
    recommendations: list[dict] = []
    try:
        rec_dir = paths.get("recommendations_dir")
        if rec_dir:
            rec_storage = RecommendationStorage(rec_dir)
            recs = rec_storage.get_top_by_score(limit=max_recommendations)
            for r in recs:
                meta = r.metadata or {}
                critic = None
                if any(meta.get(k) for k in ("confidence", "critic_challenge", "missing_context")):
                    critic = {
                        "confidence": meta.get("confidence", "Medium"),
                        "confidence_rationale": meta.get("confidence_rationale", ""),
                        "critic_challenge": meta.get("critic_challenge", ""),
                        "missing_context": meta.get("missing_context", ""),
                        "alternative": meta.get("alternative"),
                        "intel_contradictions": meta.get("intel_contradictions"),
                    }
                recommendations.append(
                    {
                        "id": r.id or "",
                        "category": r.category,
                        "title": r.title,
                        "description": r.description[:200] if r.description else "",
                        "score": r.score,
                        "status": r.status,
                        "reasoning_trace": meta.get("reasoning_trace"),
                        "critic": critic,
                    }
                )
    except Exception as e:
        logger.warning("briefing.recommendations_error", error=str(e))

    # Goals
    stale_goals: list[dict] = []
    all_goals: list[dict] = []
    try:
        tracker = GoalTracker(storage)
        raw_stale = tracker.get_stale_goals()
        stale_goals = [
            {
                "path": str(g["path"]),
                "title": g["title"],
                "status": g["status"],
                "days_since_check": g.get("days_since_check") or 0,
            }
            for g in raw_stale
        ]
        raw_all = tracker.get_goals(include_inactive=False)
        all_goals = [
            {
                "path": str(g["path"]),
                "title": g["title"],
                "status": g["status"],
                "days_since_check": g.get("days_since_check") or 0,
            }
            for g in raw_all
        ]
    except Exception as e:
        logger.warning("briefing.goals_error", error=str(e))

    # Goal-intel matches
    goal_intel_matches: list[dict] = []
    try:
        from intelligence.goal_intel_match import GoalIntelMatchStore

        db_path = paths["intel_db"]
        match_store = GoalIntelMatchStore(db_path)
        goal_paths = [g["path"] for g in all_goals]
        if goal_paths:
            goal_intel_matches = match_store.get_matches(goal_paths=goal_paths, limit=20)
    except Exception as e:
        logger.warning("briefing.goal_intel_matches_error", error=str(e))

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

        rec_list = recommendations

        brief_data = DailyBriefBuilder().build(
            stale_goals=stale_goals,
            recommendations=rec_list,
            learning_paths=[],
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
