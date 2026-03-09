"""Greeting endpoint — cached personalized greeting for chat-first home."""

import asyncio

import structlog
from fastapi import APIRouter, Depends

from advisor.context_cache import ContextCache
from advisor.greeting import (
    STATIC_FALLBACK,
    cache_greeting,
    generate_greeting,
    get_cached_greeting,
    make_greeting_cache_key,
)
from advisor.return_brief import ReturnBriefBuilder
from research.escalation import DossierEscalationEngine
from web.auth import get_current_user
from web.briefing_data import assemble_briefing_data
from web.deps import get_api_key_for_user, get_dossier_escalation_store, get_user_paths
from web.dossier_escalation_context import load_dossier_escalation_context
from web.models import GreetingResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/api/greeting", tags=["greeting"])


def _get_cache(user_id: str) -> ContextCache:
    paths = get_user_paths(user_id)
    db_path = paths["intel_db"].parent / "context_cache.db"
    return ContextCache(db_path)


def _briefing_to_greeting_context(user_id: str) -> dict:
    """Reuse shared briefing data assembly, extract greeting-relevant subset."""
    data = assemble_briefing_data(user_id)
    ctx: dict = {}

    if data["name"]:
        ctx["name"] = data["name"]

    if data["stale_goals"]:
        ctx["stale_goals"] = [
            {"title": g["title"], "days_since_check": g.get("days_since_check", 0)}
            for g in data["stale_goals"][:3]
        ]

    if data["recommendations"]:
        ctx["recommendations"] = [{"title": r["title"]} for r in data["recommendations"][:2]]

    intel_items = [{"title": m.get("title", "")} for m in data["goal_intel_matches"][:2]]
    intel_items.extend(
        {"title": item.get("title", "")} for item in (data.get("company_movements") or [])[:1]
    )
    intel_items.extend(
        {"title": item.get("title", "")} for item in (data.get("hiring_signals") or [])[:1]
    )
    intel_items.extend(
        {"title": item.get("title", "")} for item in (data.get("regulatory_alerts") or [])[:1]
    )
    intel_items = [item for item in intel_items if item.get("title")]
    if intel_items:
        ctx["intel"] = intel_items[:4]

    return ctx


async def _generate_and_cache_greeting(user_id: str) -> None:
    """Background task: assemble context, generate greeting, cache it."""
    try:
        ctx = await asyncio.to_thread(_briefing_to_greeting_context, user_id)

        api_key = get_api_key_for_user(user_id)
        if not api_key:
            logger.debug("greeting.no_api_key", user=user_id)
            return

        from llm import create_cheap_provider

        cheap_llm = create_cheap_provider(api_key=api_key)
        text = await asyncio.to_thread(generate_greeting, ctx, cheap_llm)

        cache = _get_cache(user_id)
        cache_greeting(user_id, cache, text)
        logger.info("greeting.cached", user=user_id)
    except Exception as exc:
        logger.warning("greeting.background_failed", error=str(exc), user=user_id)
        # Cache fallback briefly to avoid retry storm
        try:
            cache = _get_cache(user_id)
            key = make_greeting_cache_key(user_id)
            cache.set(key, STATIC_FALLBACK)
        except Exception:
            pass


def _schedule_greeting_refresh(user_id: str):
    """Schedule greeting generation without blocking the current request."""
    return asyncio.create_task(_generate_and_cache_greeting(user_id))


@router.get("", response_model=GreetingResponse)
async def get_greeting(user: dict = Depends(get_current_user)):
    cache = _get_cache(user["id"])
    cached_text = get_cached_greeting(user["id"], cache)
    return_brief = None

    try:
        data = assemble_briefing_data(user["id"])
        escalation_context = await load_dossier_escalation_context(
            user["id"], goals=data.get("all_goals") or [], thread_limit=3, intel_limit=20
        )
        thread_rows = escalation_context.get("threads") or []
        escalation_rows = DossierEscalationEngine(get_dossier_escalation_store(user["id"])).refresh(
            escalation_context
        )
        builder = ReturnBriefBuilder(
            data_provider=lambda _user_id: {
                "intel_matches": data.get("goal_intel_matches") or [],
                "company_movements": data.get("company_movements") or [],
                "hiring_signals": data.get("hiring_signals") or [],
                "regulatory_alerts": data.get("regulatory_alerts") or [],
                "threads": thread_rows,
                "dossiers": [
                    {
                        "id": row.get("escalation_id"),
                        "title": row.get("topic_label") or "Dossier escalation",
                        "detail": "Recurring topic now has enough momentum to deserve a dossier.",
                        "score": row.get("score"),
                    }
                    for row in escalation_rows
                ],
                "stale_goals": data.get("stale_goals") or [],
                "assumptions": data.get("assumptions") or [],
            }
        )
        return_brief = builder.build(user["id"])
    except Exception:
        return_brief = None

    if cached_text:
        return GreetingResponse(
            text=cached_text, cached=True, stale=False, return_brief=return_brief
        )

    # No cache — return fallback and generate in background
    _schedule_greeting_refresh(user["id"])
    return GreetingResponse(
        text=STATIC_FALLBACK, cached=False, stale=True, return_brief=return_brief
    )
