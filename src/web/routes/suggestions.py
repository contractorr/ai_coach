"""Unified Suggestions endpoint — merges recommendations + daily brief items."""

import structlog
from fastapi import APIRouter, Depends, Query

from advisor.why_now import WhyNowReasoner
from research.escalation import DossierEscalationEngine
from services.daily_brief import build_daily_brief_payload, load_weekly_hours
from web.auth import get_current_user
from web.briefing_data import assemble_briefing_data
from web.deps import (
    get_dossier_escalation_store,
    get_profile_storage,
    get_thread_inbox_service,
    get_watchlist_store,
)
from web.dossier_escalation_context import load_dossier_escalation_context
from web.models import SuggestionItem

logger = structlog.get_logger()

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])

_ASSUMPTION_PRIORITY = {
    "invalidated": 3,
    "confirmed": 2,
    "suggested": 1,
}

_ASSUMPTION_SCORE = {
    "invalidated": 0.95,
    "confirmed": 0.85,
    "suggested": 0.7,
}


@router.get("", response_model=list[SuggestionItem], response_model_exclude_none=True)
async def get_suggestions(
    limit: int = Query(default=10, ge=1, le=30),
    user: dict = Depends(get_current_user),
):
    """Return a unified list of suggestions combining daily brief items and recommendations."""
    data = assemble_briefing_data(user["id"])
    thread_rows = await get_thread_inbox_service(user["id"]).list_inbox(limit=10)
    watchlist_items = get_watchlist_store(user["id"]).list_items()
    reasoner = WhyNowReasoner()

    suggestions: list[SuggestionItem] = []

    # Build daily brief items as high-priority suggestions
    try:
        weekly_hours = load_weekly_hours(get_profile_storage(user["id"]))
        brief = build_daily_brief_payload(
            stale_goals=data["stale_goals"],
            recommendations=data["recommendations"],
            all_goals=data["all_goals"],
            weekly_hours=weekly_hours,
            goal_intel_matches=data["goal_intel_matches"],
        )
        for item in brief["items"]:
            suggestions.append(
                SuggestionItem(
                    source="brief",
                    kind=item["kind"],
                    title=item["title"],
                    description=item["description"],
                    action=item["action"],
                    priority=item["priority"],
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

    seen_titles = {suggestion.title for suggestion in suggestions}

    for movement in data.get("company_movements") or []:
        title = movement.get("title") or "Company movement"
        if title in seen_titles:
            continue
        seen_titles.add(title)
        suggestions.append(
            SuggestionItem(
                source="company_movement",
                kind="company_movement",
                title=title,
                description=movement.get("summary", ""),
                action="Review company movement",
                priority=1,
                score=float(movement.get("significance") or 0.0),
                payload=movement,
            )
        )

    for signal in data.get("hiring_signals") or []:
        title = signal.get("title") or "Hiring signal"
        if title in seen_titles:
            continue
        seen_titles.add(title)
        suggestions.append(
            SuggestionItem(
                source="hiring_signal",
                kind="hiring_signal",
                title=title,
                description=signal.get("summary", ""),
                action="Review hiring signal",
                priority=1,
                score=float(signal.get("strength") or 0.0),
                payload=signal,
            )
        )

    for alert in data.get("regulatory_alerts") or []:
        title = alert.get("title") or "Regulatory alert"
        if title in seen_titles:
            continue
        seen_titles.add(title)
        suggestions.append(
            SuggestionItem(
                source="regulatory_alert",
                kind="regulatory_alert",
                title=title,
                description=alert.get("summary", ""),
                action="Review regulatory alert",
                priority=2 if alert.get("urgency") == "high" else 1,
                score=float(alert.get("relevance") or 0.0),
                payload=alert,
            )
        )

    for assumption in data.get("assumptions") or []:
        title = assumption.get("title") or "Assumption alert"
        if title in seen_titles:
            continue
        seen_titles.add(title)
        status = str(assumption.get("status") or "active")
        suggestions.append(
            SuggestionItem(
                source="assumption_alert",
                kind="assumption_alert",
                title=title,
                description=assumption.get("detail", ""),
                action="Review assumption",
                priority=_ASSUMPTION_PRIORITY.get(status, 1),
                score=_ASSUMPTION_SCORE.get(status, 0.6),
                payload=assumption,
            )
        )

    for escalation in data.get("dossier_escalations") or []:
        title = escalation.get("topic_label") or "Start a dossier"
        if title in seen_titles:
            continue
        seen_titles.add(title)
        suggestions.append(
            SuggestionItem(
                source="dossier_escalation",
                kind="dossier_escalation",
                title=title,
                description="This recurring topic has enough momentum to deserve active tracking.",
                action="Start dossier",
                priority=1,
                score=float(escalation.get("score") or 0.0),
                payload=escalation,
            )
        )

    try:
        engine = DossierEscalationEngine(get_dossier_escalation_store(user["id"]))
        escalation_rows = engine.refresh(
            await load_dossier_escalation_context(
                user["id"],
                goals=data.get("all_goals") or [],
                thread_limit=10,
                intel_days=7,
                intel_limit=40,
            )
        )
        for escalation in escalation_rows:
            title = escalation.get("topic_label") or "Start a dossier"
            if title in seen_titles:
                continue
            seen_titles.add(title)
            suggestions.append(
                SuggestionItem(
                    source="dossier_escalation",
                    kind="dossier_escalation",
                    title=title,
                    description="This recurring topic has enough momentum to deserve active tracking.",
                    action="Start dossier",
                    priority=1,
                    score=float(escalation.get("score") or 0.0),
                    payload=escalation,
                )
            )
    except Exception as e:
        logger.warning("suggestions.escalation_error", error=str(e))

    context = {
        "watchlist_labels": [item.get("label") for item in watchlist_items if item.get("label")],
        "thread_labels": [item.get("label") for item in thread_rows if item.get("label")],
    }
    for index, suggestion in enumerate(suggestions):
        payload = suggestion.model_dump()
        why_now = reasoner.explain_suggestion(payload, context)
        if why_now:
            payload["why_now"] = why_now
        suggestions[index] = SuggestionItem(**payload)

    return suggestions[:limit]
