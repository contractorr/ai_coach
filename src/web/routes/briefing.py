"""Daily briefing routes — aggregates recommendations, stale goals, daily brief."""

import structlog
from fastapi import APIRouter, Depends, Query

from services.daily_brief import build_daily_brief_payload, load_weekly_hours
from web.auth import get_current_user
from web.briefing_data import assemble_briefing_data
from web.deps import get_profile_storage
from web.models import (
    AssumptionAlertResponse,
    BriefingGoal,
    BriefingRecommendation,
    BriefingResponse,
    CompanyMovementResponse,
    DossierEscalationResponse,
    GoalIntelMatch,
    HiringSignalResponse,
    RegulatoryAlertResponse,
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

    recommendations = data["recommendations"][:max_recommendations]
    stale_goals = data["stale_goals"]
    all_goals = data["all_goals"]
    goal_intel_matches = data["goal_intel_matches"]
    dossier_escalations = data.get("dossier_escalations") or []
    company_movements = data.get("company_movements") or []
    hiring_signals = data.get("hiring_signals") or []
    regulatory_alerts = data.get("regulatory_alerts") or []
    assumptions = data.get("assumptions") or []

    has_data = bool(
        recommendations
        or stale_goals
        or all_goals
        or goal_intel_matches
        or dossier_escalations
        or company_movements
        or hiring_signals
        or regulatory_alerts
        or assumptions
    )

    # Adaptation count
    adaptation_count = 0
    try:
        adaptation_count = get_feedback_count(user["id"])
    except Exception:
        pass

    # Daily brief
    daily_brief = None
    try:
        weekly_hours = load_weekly_hours(get_profile_storage(user["id"]))
        brief_data = build_daily_brief_payload(
            stale_goals=stale_goals,
            recommendations=recommendations,
            all_goals=all_goals,
            weekly_hours=weekly_hours,
            goal_intel_matches=goal_intel_matches,
        )
        daily_brief = DailyBriefModel(
            items=[DailyBriefItemModel(**item) for item in brief_data["items"]],
            budget_minutes=brief_data["budget_minutes"],
            used_minutes=brief_data["used_minutes"],
            generated_at=brief_data["generated_at"],
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
        dossier_escalations=[DossierEscalationResponse(**item) for item in dossier_escalations],
        company_movements=[CompanyMovementResponse(**item) for item in company_movements],
        hiring_signals=[HiringSignalResponse(**item) for item in hiring_signals],
        regulatory_alerts=[RegulatoryAlertResponse(**item) for item in regulatory_alerts],
        assumptions=[AssumptionAlertResponse(**item) for item in assumptions],
    )
