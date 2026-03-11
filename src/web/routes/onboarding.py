"""Onboarding chat â€” LLM-driven profile interview + goal creation."""

import asyncio
import json
import re
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException

from advisor.goals import get_goal_defaults
from journal.embeddings import EmbeddingManager
from journal.storage import JournalStorage
from llm import create_llm_provider
from web.auth import get_current_user
from web.deps import (
    SHARED_LLM_MODEL,
    enforce_onboarding_shared_key_usage_limit,
    get_config,
    get_profile_storage,
    get_user_paths,
    resolve_llm_credentials_for_user,
)
from web.feed_catalog import FEED_CATALOG, feeds_for_categories, match_categories_to_profile
from web.models import (
    FeedCategoryItem,
    OnboardingChat,
    OnboardingFeedsRequest,
    OnboardingFeedsResponse,
    OnboardingResponse,
    ProfileStatus,
)
from web.user_store import (
    add_user_rss_feed,
    clear_onboarding_responses,
    log_event,
    mark_onboarded,
    save_onboarding_turn,
    update_user_name,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

# In-memory sessions keyed by user_id
_sessions: dict[str, dict] = {}
_session_locks: dict[str, asyncio.Lock] = {}

MAX_TURNS = 15

ONBOARDING_SYSTEM = """You are a warm, curious career coach onboarding a new user. Your goal is to deeply \
understand who they are so you can give them exceptional, personalized guidance over time.

Ask one clear question at a time. Follow up on interesting answers â€” if someone mentions a startup, ask about \
stage and target market. If they mention a career transition, ask what's driving it.

You need to learn:
1. Current role/situation and career stage (junior/mid/senior/lead/exec)
2. Technical skills and proficiency levels (1-5 scale)
3. Programming languages and frameworks used
4. Professional interests and passions
5. 6-month goals (what do you want to achieve in the next 6 months?)
6. 3-year vision (where do you see yourself in 3 years?)
7. Industries and technologies they're watching or curious about
8. Time/geography/budget constraints (how many hours per week, any location constraints, budget sensitivity)
9. Fears, risks, or concerns they're navigating (job market anxiety, imposter syndrome, burnout, etc.)
10. Active projects or side projects they're working on
11. Location (city/country)
12. Preferred learning style (visual/reading/hands-on/mixed)
13. 1-3 concrete goals to track (e.g. "learn Rust", "get promoted", "launch my SaaS")

Adapt your questions based on previous answers. Group related questions when natural.
Aim for 5-8 exchanges. After gathering enough info, output EXACTLY this JSON block:

```json
{"done": true, "profile": {
  "name": "User's first/preferred name",
  "current_role": "...",
  "career_stage": "junior|mid|senior|lead|exec",
  "skills": [{"name": "...", "proficiency": 1-5}, ...],
  "languages_frameworks": ["python", "react", ...],
  "interests": ["...", ...],
  "aspirations": "...",
  "goals_short_term": "6-month goals as a sentence",
  "goals_long_term": "3-year vision as a sentence",
  "industries_watching": ["fintech", "AI/ML", ...],
  "technologies_watching": ["rust", "webassembly", ...],
  "constraints": {"time_per_week": N, "geography": "...", "budget_sensitivity": "low|medium|high"},
  "fears_risks": ["concern 1", ...],
  "active_projects": ["project 1", ...],
  "location": "...",
  "learning_style": "visual|reading|hands-on|mixed",
  "weekly_hours_available": N
}, "goals": [
  {"title": "Short goal title", "description": "Brief description of what they want to achieve"},
  ...
]}
```

Before the JSON block, include a brief friendly wrap-up message. End with: \
"Your profile will continue to deepen over time as you journal and interact with your steward."
"""

ONBOARDING_START = """Start the onboarding interview. Greet the user warmly, briefly explain you'll ask a few \
questions to understand who they are and what they're working toward, then ask your first question. Be concise \
and curious."""


def _extract_completion_json(text: str) -> dict | None:
    """Extract completion JSON with profile + goals from LLM response."""
    # Try ```json block first
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if data.get("done") and "profile" in data:
                return data
        except json.JSONDecodeError:
            pass

    # Try bare JSON
    match = re.search(r'\{"done"\s*:\s*true.*?"profile"\s*:\s*\{.*\}.*\}', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if "profile" in data:
                return data
        except json.JSONDecodeError:
            pass

    return None


def _get_session_lock(user_id: str) -> asyncio.Lock:
    lock = _session_locks.get(user_id)
    if lock is None:
        lock = asyncio.Lock()
        _session_locks[user_id] = lock
    return lock


def _normalize_message(message: str) -> str:
    normalized = message.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Message cannot be blank")
    return normalized


def _make_llm_caller(user_id: str):
    """Build LLM caller for a user (same pattern as advisor route)."""
    config = get_config()
    provider_name, api_key, source = resolve_llm_credentials_for_user(user_id)
    if not api_key:
        raise HTTPException(status_code=400, detail="No LLM API key configured")

    model = SHARED_LLM_MODEL if source == "shared" else config.llm.model
    llm = create_llm_provider(
        provider=provider_name or config.llm.provider, api_key=api_key, model=model
    )

    def caller(system: str, prompt: str, max_tokens: int = 1500) -> str:
        return llm.generate(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=max_tokens,
        )

    return caller


def _embed_profile(user_id: str, profile) -> None:
    """Embed profile summary + narrative into ChromaDB for RAG retrieval."""
    try:
        paths = get_user_paths(user_id)
        em = EmbeddingManager(paths["chroma_dir"], collection_name="profile")

        # Build narrative from profile fields
        parts = [profile.summary()]
        if profile.goals_short_term:
            parts.append(f"Short-term goals: {profile.goals_short_term}")
        if profile.goals_long_term:
            parts.append(f"Long-term vision: {profile.goals_long_term}")
        if profile.fears_risks:
            parts.append("Concerns: " + ", ".join(profile.fears_risks))
        if profile.active_projects:
            parts.append("Active projects: " + ", ".join(profile.active_projects))
        if profile.constraints:
            c = profile.constraints
            if c.get("geography"):
                parts.append(f"Geography: {c['geography']}")
            if c.get("budget_sensitivity"):
                parts.append(f"Budget sensitivity: {c['budget_sensitivity']}")

        text = "\n".join(parts)
        em.add_entry(
            f"profile:{user_id}",
            text,
            {"type": "profile", "user_id": user_id},
        )
        logger.info("onboarding.profile_embedded", user_id=user_id)
    except Exception as e:
        logger.warning("onboarding.embed_failed", user_id=user_id, error=str(e))


def _save_results(user_id: str, data: dict) -> int:
    """Save profile and create goals. Returns number of goals created."""
    paths = get_user_paths(user_id)

    # Save profile
    from profile.interview import _build_profile

    profile_data = data.get("profile", {})
    profile = _build_profile(profile_data)
    storage = get_profile_storage(user_id)
    storage.save(profile)
    logger.info("onboarding.profile_saved", user_id=user_id, skills=len(profile.skills))

    # Persist display name from interview into users DB
    onboarding_name = profile_data.get("name", "").strip()
    if onboarding_name:
        try:
            update_user_name(user_id, onboarding_name)
        except Exception as e:
            logger.warning("onboarding.name_save_failed", user_id=user_id, error=str(e))

    # Embed profile in ChromaDB
    _embed_profile(user_id, profile)

    # Create goals
    goals = data.get("goals", [])
    goals_created = 0
    if goals:
        journal_storage = JournalStorage(paths["journal_dir"])
        for g in goals:
            if isinstance(g, dict) and g.get("title"):
                try:
                    journal_storage.create(
                        content=g.get("description", ""),
                        entry_type="goal",
                        title=g["title"],
                        metadata=get_goal_defaults(),
                    )
                    goals_created += 1
                except Exception as e:
                    logger.warning("onboarding.goal_create_failed", title=g["title"], error=str(e))

    logger.info("onboarding.goals_created", user_id=user_id, count=goals_created)
    return goals_created


def _strip_json_block(text: str) -> str:
    """Remove JSON block from response text to get just the conversational part."""
    # Remove ```json...``` blocks (non-greedy across newlines)
    cleaned = re.sub(r"```(?:json)?\s*\{.*?\}\s*```", "", text, flags=re.DOTALL)
    # Remove bare {"done": true...} blocks â€” match balanced braces greedily
    cleaned = re.sub(r'\{\s*"done"\s*:\s*true.*', "", cleaned, flags=re.DOTALL)
    # Clean up leftover whitespace/newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


@router.post("/start", response_model=OnboardingResponse)
async def start_onboarding(
    user: dict = Depends(get_current_user),
    _rate_limit: None = Depends(enforce_onboarding_shared_key_usage_limit),
):
    user_id = user["id"]

    async with _get_session_lock(user_id):
        # Clear previous onboarding responses for re-onboarding
        try:
            clear_onboarding_responses(user_id)
        except Exception as e:
            logger.warning("onboarding.clear_failed", user_id=user_id, error=str(e))

        try:
            caller = _make_llm_caller(user_id)
            response = await asyncio.to_thread(caller, ONBOARDING_SYSTEM, ONBOARDING_START)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("onboarding.start_failed", user_id=user_id, error=str(e))
            raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

        _sessions[user_id] = {
            "id": uuid.uuid4().hex,
            "messages": [("assistant", response)],
            "caller": caller,
            "turns": 0,
        }

        # Persist first assistant turn
        try:
            save_onboarding_turn(user_id, 0, "assistant", response)
        except Exception as e:
            logger.warning("onboarding.persist_failed", user_id=user_id, error=str(e))

        return OnboardingResponse(message=response, done=False, turn=0)


@router.post("/chat", response_model=OnboardingResponse)
async def chat_onboarding(
    body: OnboardingChat,
    user: dict = Depends(get_current_user),
    _rate_limit: None = Depends(enforce_onboarding_shared_key_usage_limit),
):
    user_id = user["id"]

    async with _get_session_lock(user_id):
        session = _sessions.get(user_id)
        if not session:
            raise HTTPException(
                status_code=400, detail="No active onboarding session â€” call /start first"
            )

        message = _normalize_message(body.message)
        session["messages"].append(("user", message))
        session["turns"] += 1
        turn = session["turns"]

        # Persist user turn
        try:
            save_onboarding_turn(user_id, turn, "user", message)
        except Exception as e:
            logger.warning("onboarding.persist_failed", user_id=user_id, error=str(e))

        # Build conversation history
        history = "\n".join(
            f"{'Coach' if role == 'assistant' else 'User'}: {msg}"
            for role, msg in session["messages"]
        )

        force = session["turns"] >= MAX_TURNS
        if force:
            prompt = f"""Based on this interview, generate the profile and goals JSON now.

{history}

Output the JSON block now with whatever information you have."""
        else:
            prompt = f"Interview so far:\n{history}\n\nContinue the interview or finalize if you have enough info."

        caller = session["caller"]
        try:
            response = await asyncio.to_thread(caller, ONBOARDING_SYSTEM, prompt, max_tokens=2000)
        except Exception as e:
            logger.error("onboarding.chat_failed", user_id=user_id, error=str(e))
            raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

        # Check for completion JSON
        completion = _extract_completion_json(response)
        if completion:
            try:
                goals_created = _save_results(user_id, completion)
            except Exception as e:
                logger.error("onboarding.save_failed", user_id=user_id, error=str(e))
                goals_created = 0
            _sessions.pop(user_id, None)
            clean_msg = _strip_json_block(response)
            if not clean_msg:
                clean_msg = "Great, I've got everything I need! Your profile is set up and will continue to deepen over time."
            mark_onboarded(user_id)
            log_event(
                "onboarding_complete", user_id, {"goals_created": goals_created, "turns": turn}
            )
            return OnboardingResponse(
                message=clean_msg, done=True, goals_created=goals_created, turn=turn
            )

        session["messages"].append(("assistant", response))

        # Persist assistant turn
        try:
            save_onboarding_turn(user_id, turn, "assistant", response)
        except Exception as e:
            logger.warning("onboarding.persist_failed", user_id=user_id, error=str(e))

        # Force extraction if we hit max turns and LLM didn't include JSON
        if force:
            force_prompt = f"""{history}

Coach: {response}

Now output ONLY the JSON block with profile and goals based on everything discussed."""
            goals_created = 0
            try:
                force_response = await asyncio.to_thread(
                    caller, ONBOARDING_SYSTEM, force_prompt, max_tokens=2000
                )
                completion = _extract_completion_json(force_response)
                if completion:
                    try:
                        goals_created = _save_results(user_id, completion)
                    except Exception as e:
                        logger.error("onboarding.save_failed", user_id=user_id, error=str(e))
                else:
                    logger.warning("onboarding.force_finalize_no_completion", user_id=user_id)
            except Exception as e:
                logger.error("onboarding.force_finalize_failed", user_id=user_id, error=str(e))
            finally:
                _sessions.pop(user_id, None)

            mark_onboarded(user_id)
            log_event(
                "onboarding_complete", user_id, {"goals_created": goals_created, "turns": turn}
            )
            return OnboardingResponse(
                message=response, done=True, goals_created=goals_created, turn=turn
            )

        return OnboardingResponse(message=response, done=False, turn=turn)


@router.get("/feed-categories", response_model=list[FeedCategoryItem])
async def get_feed_categories(user: dict = Depends(get_current_user)):
    """Return all feed categories with pre-selections based on user profile."""
    user_id = user["id"]
    profile = get_profile_storage(user_id).load()

    if profile:
        preselected = set(
            match_categories_to_profile(
                interests=profile.interests,
                industries=profile.industries_watching,
                technologies=profile.technologies_watching,
                languages=profile.languages_frameworks,
            )
        )
    else:
        preselected = {"general_tech"}

    return [
        FeedCategoryItem(
            id=cat.id,
            label=cat.label,
            icon=cat.icon,
            feed_count=len(cat.feeds),
            preselected=cat.id in preselected,
        )
        for cat in FEED_CATALOG
    ]


@router.post("/feeds", response_model=OnboardingFeedsResponse)
async def set_onboarding_feeds(
    body: OnboardingFeedsRequest,
    user: dict = Depends(get_current_user),
):
    """Bulk-insert RSS feeds for selected categories. Idempotent via UPSERT."""
    user_id = user["id"]
    selected = body.selected_category_ids

    feeds = feeds_for_categories(selected)
    added = 0
    for feed in feeds:
        try:
            add_user_rss_feed(user_id, feed["url"], feed["name"], added_by="onboarding")
            added += 1
        except Exception as e:
            logger.warning("onboarding.feed_add_failed", url=feed["url"], error=str(e))

    log_event("onboarding_feeds", user_id, {"feeds_added": added, "categories": selected})
    return OnboardingFeedsResponse(feeds_added=added, categories=selected)


@router.get("/profile-status", response_model=ProfileStatus)
async def get_profile_status(user: dict = Depends(get_current_user)):
    """Check if user has a profile, if it's stale, and if they have an API key."""
    user_id = user["id"]
    profile = get_profile_storage(user_id).load()

    _provider, _key, source = resolve_llm_credentials_for_user(user_id)

    return ProfileStatus(
        has_profile=profile is not None,
        is_stale=profile.is_stale() if profile else False,
        has_api_key=_key is not None,
        has_own_key=source == "user",
        using_shared_key=source == "shared",
    )
