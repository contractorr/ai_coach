"""Personalized greeting generation with SQLite cache."""

import structlog

from advisor.context_cache import ContextCache
from storage_paths import safe_user_id

logger = structlog.get_logger()

GREETING_TTL = 14400  # 4 hours
GREETING_ERROR_TTL = 300  # 5 min fallback on LLM failure

STATIC_FALLBACK = (
    "Welcome back. I'm here to help you think through decisions, "
    "track your goals, and stay on top of what matters in your field. "
    "Ask me anything or capture a quick thought."
)

GREETING_PROMPT_SYSTEM = (
    "You are a concise personal career advisor. Write a personalized greeting "
    "for the user in 3-5 sentences. Reference their current situation — stale goals, "
    "recent recommendations, or notable intel — to show you're aware of their context. "
    "Be warm but direct. Do NOT use bullet points or headers. Do NOT start with 'Hello' "
    "or 'Hi' — jump straight into substance."
)


def make_greeting_cache_key(user_id: str) -> str:
    return f"greeting_v1_{safe_user_id(user_id)}"


def _build_greeting_prompt(briefing_ctx: dict) -> str:
    """Build user-turn prompt from lightweight briefing context."""
    parts = []
    name = briefing_ctx.get("name")
    if name:
        parts.append(f"User's name: {name}")

    stale_goals = briefing_ctx.get("stale_goals") or []
    if stale_goals:
        goals_text = "; ".join(
            f"{g['title']} ({g.get('days_since_check', '?')}d since check-in)"
            for g in stale_goals[:3]
        )
        parts.append(f"Stale goals: {goals_text}")

    recs = briefing_ctx.get("recommendations") or []
    if recs:
        recs_text = "; ".join(r.get("title", "") for r in recs[:2])
        parts.append(f"Top recommendations: {recs_text}")

    intel = briefing_ctx.get("intel") or []
    if intel:
        intel_text = "; ".join(i.get("title", "") for i in intel[:2])
        parts.append(f"Recent intel: {intel_text}")

    if not parts:
        parts.append("No context available yet — this is a new or sparse user.")

    return "\n".join(parts)


def generate_greeting(briefing_ctx: dict, cheap_llm) -> str:
    """Generate greeting via cheap LLM. Returns text or STATIC_FALLBACK on error."""
    try:
        user_prompt = _build_greeting_prompt(briefing_ctx)
        response = cheap_llm.ask(
            user_prompt,
            system_prompt=GREETING_PROMPT_SYSTEM,
            max_tokens=200,
        )
        text = response.strip() if response else ""
        return text or STATIC_FALLBACK
    except Exception as exc:
        logger.warning("greeting.generate_failed", error=str(exc))
        return STATIC_FALLBACK


def get_cached_greeting(user_id: str, cache: ContextCache) -> str | None:
    key = make_greeting_cache_key(user_id)
    return cache.get(key, ttl=GREETING_TTL)


def cache_greeting(user_id: str, cache: ContextCache, text: str):
    key = make_greeting_cache_key(user_id)
    cache.set(key, text)


def invalidate_greeting(user_id: str, cache: ContextCache):
    key = make_greeting_cache_key(user_id)
    cache.invalidate(key)
