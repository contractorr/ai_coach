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
from web.auth import get_current_user
from web.briefing_data import assemble_briefing_data
from web.deps import get_api_key_for_user, get_thread_inbox_service, get_user_paths
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

    # Recent intel from goal-intel matches (top 2)
    if data["goal_intel_matches"]:
        ctx["intel"] = [{"title": m.get("title", "")} for m in data["goal_intel_matches"][:2]]

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
        thread_rows = await get_thread_inbox_service(user["id"]).list_inbox(limit=3)
        builder = ReturnBriefBuilder(
            data_provider=lambda _user_id: {
                "intel_matches": data.get("goal_intel_matches") or [],
                "threads": thread_rows,
                "dossiers": [],
                "stale_goals": data.get("stale_goals") or [],
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
