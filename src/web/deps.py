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
    create_mind_map_store,
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
from web.user_store import get_user_secrets, is_onboarded

logger = structlog.get_logger()

SUPPORTED_LLM_PROVIDERS = ("claude", "openai", "gemini")
LLM_PROVIDER_ENV_KEYS = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}

SECRET_KEY_FIELDS = [
    "llm_api_key",
    "llm_api_key_claude",
    "llm_api_key_openai",
    "llm_api_key_gemini",
    "tavily_api_key",
    "github_token",
    "github_pat",
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


def get_mind_map_store(user_id: str):
    """Construct the per-user journal mind-map store."""
    return create_mind_map_store(get_user_paths(user_id))


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


def get_github_repo_store():
    """Construct the shared GitHub repo monitoring store."""
    from intelligence.github_repo_store import GitHubRepoStore

    return GitHubRepoStore(get_coach_paths()["intel_db"])


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


def get_library_index(user_id: str):
    """Construct the per-user library index with semantic search."""
    from library.embeddings import LibraryEmbeddingManager
    from library.index import LibraryIndex

    paths = get_user_paths(user_id)
    config = get_config()
    config_dict = config.to_dict() if hasattr(config, "to_dict") else None
    embeddings = LibraryEmbeddingManager(paths["chroma_dir"], config=config_dict)
    return LibraryIndex(Path(paths["data_dir"]) / "library", embedding_manager=embeddings)


def get_insight_store():
    """Construct the shared insight store."""
    return create_insight_store(get_coach_paths())


# --- Per-user secrets ---


def get_decrypted_secrets_for_user(user_id: str) -> dict:
    """Load all decrypted secrets for a specific user."""
    return get_user_secrets(user_id, get_secret_key())


SHARED_LLM_MODEL = "claude-haiku-4-5"


def llm_secret_key(provider: str) -> str:
    """Return the per-provider secret key name."""
    return f"llm_api_key_{provider}"


def _normalize_llm_provider(provider: str | None) -> str | None:
    if not provider:
        return None
    provider = provider.lower().strip()
    if provider == "auto":
        return "auto"
    if provider in SUPPORTED_LLM_PROVIDERS:
        return provider
    return None


def _parse_bool_secret(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def resolve_feature_toggle(
    secrets: dict[str, str],
    feature_key: str,
    config_default: bool,
) -> bool:
    """User secret takes precedence; falls back to global config value."""
    raw = secrets.get(feature_key)
    if raw is None:
        return config_default
    return _parse_bool_secret(raw, default=config_default)


def _detect_provider_from_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if api_key.startswith("sk-ant-"):
        return "claude"
    if api_key.startswith("sk-"):
        return "openai"
    if api_key.startswith("AIza"):
        return "gemini"
    return None


def _get_personal_llm_keys_from_secrets(secrets: dict[str, str]) -> dict[str, str]:
    keys: dict[str, str] = {}
    for provider in SUPPORTED_LLM_PROVIDERS:
        value = secrets.get(llm_secret_key(provider))
        if value:
            keys[provider] = value

    if keys:
        return keys

    legacy_key = secrets.get("llm_api_key")
    if legacy_key:
        provider = _normalize_llm_provider(secrets.get("llm_provider"))
        if provider in SUPPORTED_LLM_PROVIDERS:
            keys[provider] = legacy_key
        else:
            inferred = _detect_provider_from_key(legacy_key)
            if inferred:
                keys[inferred] = legacy_key
    return keys


def get_personal_llm_keys_for_user(user_id: str) -> dict[str, str]:
    """Return configured personal LLM API keys keyed by provider."""
    return _get_personal_llm_keys_from_secrets(get_decrypted_secrets_for_user(user_id))


def _get_shared_llm_key(provider: str | None = None) -> tuple[str | None, str | None]:
    if provider and provider in LLM_PROVIDER_ENV_KEYS:
        value = os.getenv(LLM_PROVIDER_ENV_KEYS[provider])
        if value:
            return value, provider

    for candidate in SUPPORTED_LLM_PROVIDERS:
        env_var = LLM_PROVIDER_ENV_KEYS[candidate]
        value = os.getenv(env_var)
        if value:
            return value, candidate

    config = get_config()
    if config.llm.api_key:
        configured = _normalize_llm_provider(config.llm.provider) or provider or "claude"
        return config.llm.api_key, configured

    return None, None


def resolve_llm_credentials_for_user(
    user_id: str,
    provider: str | None = None,
) -> tuple[str | None, str | None, str | None]:
    """Resolve (provider, api_key, source) for a user's normal single-provider LLM call."""
    config = get_config()
    secrets = get_decrypted_secrets_for_user(user_id)
    personal_keys = _get_personal_llm_keys_from_secrets(secrets)
    preferred = (
        _normalize_llm_provider(provider)
        or _normalize_llm_provider(secrets.get("llm_provider"))
        or _normalize_llm_provider(config.llm.provider)
    )

    if preferred in SUPPORTED_LLM_PROVIDERS and personal_keys.get(preferred):
        return preferred, personal_keys[preferred], "user"

    if preferred == "auto" or preferred is None:
        for candidate in SUPPORTED_LLM_PROVIDERS:
            if personal_keys.get(candidate):
                return candidate, personal_keys[candidate], "user"

    if preferred in SUPPORTED_LLM_PROVIDERS:
        shared_key, shared_provider = _get_shared_llm_key(preferred)
        if shared_key:
            return shared_provider, shared_key, "shared"

    for candidate in SUPPORTED_LLM_PROVIDERS:
        if personal_keys.get(candidate):
            return candidate, personal_keys[candidate], "user"

    shared_key, shared_provider = _get_shared_llm_key(preferred)
    if shared_key:
        return shared_provider, shared_key, "shared"

    return preferred if preferred in SUPPORTED_LLM_PROVIDERS else None, None, None


def get_custom_providers_for_user(user_id: str) -> list[dict[str, str]]:
    """Return user's custom OpenAI-compatible provider configs."""
    import json

    secrets = get_decrypted_secrets_for_user(user_id)
    raw = secrets.get("llm_custom_providers")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []


def get_council_members_for_user(user_id: str) -> list[dict[str, str]]:
    """Return configured personal provider credentials eligible for council mode."""
    secrets = get_decrypted_secrets_for_user(user_id)
    enabled = _parse_bool_secret(secrets.get("llm_council_enabled"), default=True)
    if not enabled:
        return []

    members = []

    # Add built-in providers
    for provider, api_key in _get_personal_llm_keys_from_secrets(secrets).items():
        if api_key:
            members.append({"provider": provider, "api_key": api_key})

    # Add custom providers
    for custom in get_custom_providers_for_user(user_id):
        members.append(
            {
                "provider": "openai_compatible",
                "api_key": custom["api_key"],
                "model": custom["model"],
                "display_name": custom["display_name"],
                "base_url": custom["base_url"],
            }
        )

    return members


def get_api_key_with_source(user_id: str) -> tuple[str | None, str | None]:
    """Get LLM API key + source for a user.

    Returns (key, source) where source is "user" | "shared" | None.
    """
    _provider, api_key, source = resolve_llm_credentials_for_user(user_id)
    return api_key, source


def get_api_key_for_user(user_id: str, provider: str | None = None) -> str | None:
    """Get LLM API key for a user: user secrets first, then env vars, then config."""
    _provider, api_key, _source = resolve_llm_credentials_for_user(user_id, provider=provider)
    return api_key


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
    personal_keys = _get_personal_llm_keys_from_secrets(secrets)
    provider_statuses = [
        {
            "provider": provider,
            "configured": bool(personal_keys.get(provider)),
            "hint": _hint(personal_keys.get(provider)),
            "council_eligible": bool(personal_keys.get(provider)),
        }
        for provider in SUPPORTED_LLM_PROVIDERS
    ]

    selected_provider, _key, source = resolve_llm_credentials_for_user(user_id)
    has_own_key = bool(personal_keys)
    preferred_provider = _normalize_llm_provider(secrets.get("llm_provider")) or config.llm.provider
    display_provider = preferred_provider if preferred_provider != "auto" else selected_provider
    key_hint = None
    if display_provider in personal_keys:
        key_hint = _hint(personal_keys.get(display_provider))
    elif personal_keys:
        key_hint = _hint(next(iter(personal_keys.values())))
    council_enabled = _parse_bool_secret(secrets.get("llm_council_enabled"), default=True)
    has_profile = is_onboarded(user_id)
    custom_providers = get_custom_providers_for_user(user_id)
    custom_provider_infos = [
        {
            "id": cp["id"],
            "display_name": cp["display_name"],
            "base_url": cp["base_url"],
            "model": cp["model"],
        }
        for cp in custom_providers
    ]
    total_providers = len(personal_keys) + len(custom_providers)

    return {
        "has_profile": has_profile,
        "llm_provider": display_provider,
        "llm_model": secrets.get("llm_model") or config.llm.model,
        "llm_council_enabled": council_enabled,
        "llm_council_ready": council_enabled and total_providers >= 2,
        "llm_provider_keys": provider_statuses,
        "llm_custom_providers": custom_provider_infos,
        "llm_api_key_set": has_own_key,
        "llm_api_key_hint": key_hint,
        "using_shared_key": source == "shared",
        "has_own_key": has_own_key,
        "tavily_api_key_set": bool(secrets.get("tavily_api_key")),
        "tavily_api_key_hint": _hint(secrets.get("tavily_api_key")),
        "github_token_set": bool(secrets.get("github_token")),
        "github_token_hint": _hint(secrets.get("github_token")),
        "github_pat_set": bool(secrets.get("github_pat")),
        "github_pat_hint": _hint(secrets.get("github_pat")),
        "eventbrite_token_set": bool(secrets.get("eventbrite_token")),
        # Feature toggles
        "feature_extended_thinking": resolve_feature_toggle(
            secrets, "feature_extended_thinking", config.llm.extended_thinking
        ),
        "feature_memory_enabled": resolve_feature_toggle(
            secrets, "feature_memory_enabled", config.memory.enabled
        ),
        "feature_threads_enabled": resolve_feature_toggle(
            secrets, "feature_threads_enabled", config.threads.enabled
        ),
        "feature_recommendations_enabled": resolve_feature_toggle(
            secrets, "feature_recommendations_enabled", config.recommendations.enabled
        ),
        "feature_research_enabled": resolve_feature_toggle(
            secrets, "feature_research_enabled", config.research.enabled
        ),
        "feature_entity_extraction_enabled": resolve_feature_toggle(
            secrets, "feature_entity_extraction_enabled", True
        ),
        "feature_trending_radar_enabled": resolve_feature_toggle(
            secrets, "feature_trending_radar_enabled", config.trending_radar.enabled
        ),
        "feature_heartbeat_enabled": resolve_feature_toggle(
            secrets, "feature_heartbeat_enabled", config.heartbeat.enabled
        ),
        "feature_company_movement_enabled": resolve_feature_toggle(
            secrets, "feature_company_movement_enabled", config.company_movement.enabled
        ),
        "feature_hiring_signals_enabled": resolve_feature_toggle(
            secrets, "feature_hiring_signals_enabled", config.hiring.enabled
        ),
        "feature_regulatory_signals_enabled": resolve_feature_toggle(
            secrets, "feature_regulatory_signals_enabled", config.regulatory.enabled
        ),
        "feature_github_monitoring": resolve_feature_toggle(
            secrets, "feature_github_monitoring", config.github_monitoring.enabled
        ),
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
