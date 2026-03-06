"""Greeting endpoint — cached personalized greeting for chat-first home."""

import asyncio
from pathlib import Path

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
from web.auth import get_current_user
from web.deps import get_api_key_for_user, get_user_paths
from web.models import GreetingResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/api/greeting", tags=["greeting"])


def _get_cache(user_id: str) -> ContextCache:
    paths = get_user_paths(user_id)
    db_path = paths["intel_db"].parent / "context_cache.db"
    return ContextCache(db_path)


def _assemble_greeting_context(user_id: str) -> dict:
    """Lightweight context assembly — profile name, stale goals, top recs, recent intel."""
    paths = get_user_paths(user_id)
    ctx: dict = {}

    # Profile name
    try:
        from profile.storage import ProfileStorage

        profile_path = paths.get("profile")
        if profile_path and Path(profile_path).exists():
            prof = ProfileStorage(profile_path).load()
            if prof:
                ctx["name"] = getattr(prof, "name", None) or getattr(prof, "current_role", "")
    except Exception:
        pass

    # Stale goals (top 3)
    try:
        from advisor.goals import GoalTracker
        from journal.storage import JournalStorage

        storage = JournalStorage(paths["journal_dir"])
        tracker = GoalTracker(storage)
        stale = tracker.get_stale_goals()
        ctx["stale_goals"] = [
            {
                "title": g["title"],
                "days_since_check": g.get("days_since_check", 0),
            }
            for g in stale[:3]
        ]
    except Exception:
        pass

    # Top recommendations (2)
    try:
        from advisor.recommendation_storage import RecommendationStorage

        rec_dir = paths.get("recommendations_dir")
        if rec_dir and Path(rec_dir).exists():
            rec_storage = RecommendationStorage(rec_dir)
            recs = rec_storage.get_top_by_score(limit=2)
            ctx["recommendations"] = [{"title": r.title} for r in recs]
    except Exception:
        pass

    # Recent intel (2)
    try:
        from intelligence.scraper import IntelStorage

        intel_db = paths["intel_db"]
        if Path(intel_db).exists():
            intel_storage = IntelStorage(intel_db)
            items = intel_storage.get_recent(limit=2)
            ctx["intel"] = [{"title": i.get("title", "")} for i in items]
    except Exception:
        pass

    return ctx


async def _generate_and_cache_greeting(user_id: str) -> None:
    """Background task: assemble context, generate greeting, cache it."""
    try:
        ctx = await asyncio.to_thread(_assemble_greeting_context, user_id)

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


@router.get("", response_model=GreetingResponse)
async def get_greeting(user: dict = Depends(get_current_user)):
    cache = _get_cache(user["id"])
    cached_text = get_cached_greeting(user["id"], cache)

    if cached_text:
        return GreetingResponse(text=cached_text, cached=True, stale=False)

    # No cache — return fallback and generate in background
    asyncio.create_task(_generate_and_cache_greeting(user["id"]))
    return GreetingResponse(text=STATIC_FALLBACK, cached=False, stale=True)
