"""Dependency injection for FastAPI routes."""

import os
from functools import lru_cache
from pathlib import Path

import structlog
from fastapi import Depends, HTTPException

from coach_config import get_paths, load_config_model
from storage_access import (
    create_follow_up_store,
    create_insight_store,
    create_intel_storage,
    create_memory_store,
    create_profile_embedding_manager,
    create_profile_storage,
    create_recommendation_storage,
    create_thread_store,
    create_watchlist_store,
)
from storage_access import (
    get_profile_path as resolve_profile_path,
)
from storage_paths import get_user_paths as resolve_user_paths
from storage_paths import safe_user_id as _safe_user_id
from web.auth import get_current_user
from web.rate_limit import check_shared_key_rate_limit
from web.user_store import get_user_secrets

logger = structlog.get_logger()

SECRET_KEY_FIELDS = [
    "llm_api_key",
    "tavily_api_key",
    "github_token",
    "eventbrite_token",
]


@lru_cache
def get_config():
    """Load shared config from ~/coach/config.yaml."""
    return load_config_model()


def get_coach_paths() -> dict:
    """Get expanded paths dict (CLI / legacy single-user)."""
    coach_home = os.getenv("COACH_HOME")
    if coach_home:
        base = Path(coach_home).expanduser()
        return {
            "journal_dir": base / "journal",
            "chroma_dir": base / "chroma",
            "intel_db": base / "intel.db",
            "log_file": base / "coach.log",
        }

    config = get_config()
    return get_paths(config.to_dict())


def get_secret_key() -> str:
    """Get Fernet secret key from env."""
    key = os.getenv("SECRET_KEY")
    if not key:
        raise RuntimeError("SECRET_KEY env var required for API key encryption")
    return key


# --- Per-user paths ---


def safe_user_id(user_id: str) -> str:
    """Sanitize user_id for use in file paths and collection names."""
    return _safe_user_id(user_id)


def get_user_paths(user_id: str) -> dict:
    """Per-user data directories under ~/coach/users/{user_id}/."""
    return resolve_user_paths(user_id)


def get_profile_path(user_id: str):
    """Get the canonical profile path for a user."""
    return resolve_profile_path(get_user_paths(user_id))


def get_profile_storage(user_id: str):
    """Construct the per-user profile store."""
    return create_profile_storage(get_user_paths(user_id))


def get_profile_embedding_manager(user_id: str):
    """Construct the embedding manager used for profile indexing."""
    return create_profile_embedding_manager(get_user_paths(user_id))


def get_memory_store(user_id: str):
    """Construct the per-user memory store."""
    return create_memory_store(get_user_paths(user_id))


def get_thread_store(user_id: str):
    """Construct the per-user thread store."""
    return create_thread_store(get_user_paths(user_id))


def get_receipt_store(user_id: str):
    """Construct the per-user extraction receipt store."""
    from journal.extraction_receipts import ExtractionReceiptStore

    return ExtractionReceiptStore(get_user_paths(user_id)["receipts_db"])


def get_thread_inbox_state_store(user_id: str):
    """Construct the per-user thread inbox state store."""
    from journal.thread_inbox import ThreadInboxStateStore

    return ThreadInboxStateStore(get_user_paths(user_id)["threads_db"])


def get_thread_inbox_service(user_id: str):
    """Construct the merged recurring-thread inbox service."""
    from journal.storage import JournalStorage
    from journal.thread_inbox import ThreadInboxService

    paths = get_user_paths(user_id)
    return ThreadInboxService(
        create_thread_store(paths),
        get_thread_inbox_state_store(user_id),
        JournalStorage(paths["journal_dir"]),
    )


def get_intel_storage():
    """Construct the shared intel storage."""
    return create_intel_storage(get_coach_paths())


def get_watchlist_store(user_id: str):
    """Construct the per-user watchlist store."""
    return create_watchlist_store(get_user_paths(user_id))


def get_follow_up_store(user_id: str):
    """Construct the per-user follow-up store."""
    return create_follow_up_store(get_user_paths(user_id))


def get_recommendation_storage(user_id: str):
    """Construct the per-user recommendation store."""
    return create_recommendation_storage(get_user_paths(user_id))


def get_dossier_escalation_store(user_id: str):
    """Construct the per-user dossier escalation store."""
    from research.escalation import DossierEscalationStore

    return DossierEscalationStore(get_user_paths(user_id)["escalations_db"])


def get_outcome_store(user_id: str):
    """Construct the per-user harvested outcome store."""
    from advisor.outcomes import HarvestedOutcomeStore

    return HarvestedOutcomeStore(get_user_paths(user_id)["outcomes_db"])


def get_assumption_store(user_id: str):
    """Construct the per-user assumption store."""
    from advisor.assumptions import AssumptionStore

    return AssumptionStore(get_user_paths(user_id)["assumptions_db"])


def get_company_movement_store():
    """Construct the shared company movement store."""
    from intelligence.company_watch import CompanyMovementStore

    return CompanyMovementStore(get_coach_paths()["intel_db"])


def get_hiring_signal_store():
    """Construct the shared hiring signal store."""
    from intelligence.hiring_signals import HiringSignalStore

    return HiringSignalStore(get_coach_paths()["intel_db"])


def get_hiring_baseline_tracker():
    """Construct the shared hiring baseline tracker."""
    from intelligence.hiring_signals import HiringBaselineTracker

    return HiringBaselineTracker(get_coach_paths()["intel_db"])


def get_regulatory_alert_store():
    """Construct the shared regulatory alert store."""
    from intelligence.regulatory import RegulatoryAlertStore

    return RegulatoryAlertStore(get_coach_paths()["intel_db"])


def get_insight_store():
    """Construct the shared insight store."""
    return create_insight_store(get_coach_paths())


# --- Per-user secrets ---


def get_decrypted_secrets_for_user(user_id: str) -> dict:
    """Load all decrypted secrets for a specific user."""
    return get_user_secrets(user_id, get_secret_key())


SHARED_LLM_MODEL = "claude-haiku-4-5"


def get_api_key_with_source(user_id: str) -> tuple[str | None, str | None]:
    """Get LLM API key + source for a user.

    Returns (key, source) where source is "user" | "shared" | None.
    """
    secrets = get_decrypted_secrets_for_user(user_id)

    if secrets.get("llm_api_key"):
        return secrets["llm_api_key"], "user"

    for env_var in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"]:
        val = os.getenv(env_var)
        if val:
            return val, "shared"

    config = get_config()
    if config.llm.api_key:
        return config.llm.api_key, "shared"

    return None, None


def get_api_key_for_user(user_id: str, provider: str | None = None) -> str | None:
    """Get LLM API key for a user: user secrets first, then env vars, then config."""
    key, _source = get_api_key_with_source(user_id)
    return key


def enforce_shared_key_usage_limit(user: dict = Depends(get_current_user)) -> None:
    """Apply the shared-key rate limit when a user is on the shared key path."""
    _key, source = get_api_key_with_source(user["id"])
    if source == "shared":
        check_shared_key_rate_limit(user["id"])


def enforce_onboarding_shared_key_usage_limit(user: dict = Depends(get_current_user)) -> None:
    """Apply the onboarding-specific shared-key rate limit when needed."""
    _key, source = get_api_key_with_source(user["id"])
    if source == "shared":
        check_shared_key_rate_limit(user["id"], onboarding=True)


def require_personal_research_key(user: dict = Depends(get_current_user)) -> None:
    """Block deep research for shared-key users where quality is intentionally gated."""
    _key, source = get_api_key_with_source(user["id"])
    if source == "shared":
        raise HTTPException(
            status_code=403,
            detail="Deep research requires your own API key. Add one in Settings to unlock.",
        )


def _hint(value: str | None) -> str | None:
    """Return last 4 chars as hint, or None."""
    if not value or len(value) < 4:
        return None
    return f"...{value[-4:]}"


def get_settings_mask_for_user(user_id: str) -> dict:
    """Return settings with bool mask for secrets, per-user."""
    secrets = get_decrypted_secrets_for_user(user_id)
    config = get_config()

    _key, source = get_api_key_with_source(user_id)
    has_own_key = bool(secrets.get("llm_api_key"))

    return {
        "llm_provider": secrets.get("llm_provider") or config.llm.provider,
        "llm_model": secrets.get("llm_model") or config.llm.model,
        "llm_api_key_set": has_own_key,
        "llm_api_key_hint": _hint(secrets.get("llm_api_key")),
        "using_shared_key": source == "shared",
        "has_own_key": has_own_key,
        "tavily_api_key_set": bool(secrets.get("tavily_api_key")),
        "tavily_api_key_hint": _hint(secrets.get("tavily_api_key")),
        "github_token_set": bool(secrets.get("github_token")),
        "github_token_hint": _hint(secrets.get("github_token")),
        "eventbrite_token_set": bool(secrets.get("eventbrite_token")),
    }


# --- Legacy single-user compat (used by old tests / CLI) ---


def get_decrypted_secrets() -> dict:
    """Load all decrypted secrets from legacy file."""
    from web.crypto import load_secrets

    return load_secrets(get_secret_key())


def get_api_key_for_provider(provider: str | None = None) -> str | None:
    """Legacy: get API key from file-based secrets."""
    secrets = get_decrypted_secrets()
    if secrets.get("llm_api_key"):
        return secrets["llm_api_key"]
    for env_var in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"]:
        val = os.getenv(env_var)
        if val:
            return val
    config = get_config()
    if config.llm.api_key:
        return config.llm.api_key
    return None


def get_settings_mask() -> dict:
    """Legacy single-user settings mask."""
    secrets = get_decrypted_secrets()
    config = get_config()
    return {
        "llm_provider": secrets.get("llm_provider") or config.llm.provider,
        "llm_model": secrets.get("llm_model") or config.llm.model,
        "llm_api_key_set": bool(secrets.get("llm_api_key")),
        "llm_api_key_hint": _hint(secrets.get("llm_api_key")),
        "tavily_api_key_set": bool(secrets.get("tavily_api_key")),
        "tavily_api_key_hint": _hint(secrets.get("tavily_api_key")),
        "github_token_set": bool(secrets.get("github_token")),
        "github_token_hint": _hint(secrets.get("github_token")),
        "eventbrite_token_set": bool(secrets.get("eventbrite_token")),
    }
