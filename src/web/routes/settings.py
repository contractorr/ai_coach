"""API key and settings management routes (per-user)."""

import asyncio

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from web.auth import get_current_user
from web.deps import (
    SUPPORTED_LLM_PROVIDERS,
    get_secret_key,
    get_settings_mask_for_user,
    llm_secret_key,
    resolve_llm_credentials_for_user,
)
from web.models import SettingsResponse, SettingsUpdate, UsageStatsResponse
from web.user_store import (
    delete_user_secret,
    get_user_secret,
    get_user_usage_stats,
    set_user_secret,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api/settings", tags=["settings"])

FEATURE_TOGGLE_FIELDS = [
    "feature_extended_thinking",
    "feature_memory_enabled",
    "feature_threads_enabled",
    "feature_recommendations_enabled",
    "feature_research_enabled",
    "feature_entity_extraction_enabled",
    "feature_trending_radar_enabled",
    "feature_heartbeat_enabled",
    "feature_company_movement_enabled",
    "feature_hiring_signals_enabled",
    "feature_regulatory_signals_enabled",
    "feature_github_monitoring",
]


def _detect_provider_from_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if api_key.startswith("sk-ant-"):
        return "claude"
    if api_key.startswith("sk-"):
        return "openai"
    if api_key.startswith("AI"):
        return "gemini"
    return None


def _legacy_provider(body: SettingsUpdate) -> str:
    requested = (body.llm_provider or "").strip().lower()
    if requested in SUPPORTED_LLM_PROVIDERS:
        return requested
    inferred = _detect_provider_from_key(body.llm_api_key)
    if inferred:
        return inferred
    return "openai"


def _clear_personal_llm_keys(user_id: str) -> list[str]:
    removed: list[str] = []
    for provider in SUPPORTED_LLM_PROVIDERS:
        delete_user_secret(user_id, llm_secret_key(provider))
        removed.append(f"remove:{provider}")
    delete_user_secret(user_id, "llm_api_key")
    return removed


def _get_stored_provider_key(user_id: str, provider: str, fernet_key: str) -> str | None:
    provider_key = get_user_secret(user_id, llm_secret_key(provider), fernet_key)
    if provider_key:
        return provider_key

    legacy_key = get_user_secret(user_id, "llm_api_key", fernet_key)
    if legacy_key:
        legacy_provider = get_user_secret(user_id, "llm_provider", fernet_key)
        inferred = legacy_provider or _detect_provider_from_key(legacy_key)
        if inferred == provider:
            return legacy_key
    return None


@router.get("", response_model=SettingsResponse)
async def get_settings(user: dict = Depends(get_current_user)):
    """Return per-user settings with bool mask for secrets."""
    mask = get_settings_mask_for_user(user["id"])
    logger.info(
        "settings.get",
        user_id=user["id"],
        keys_set={k: v for k, v in mask.items() if k.endswith("_set")},
    )
    return SettingsResponse(**mask)


@router.put("", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdate,
    user: dict = Depends(get_current_user),
):
    """Encrypt and save per-user settings."""
    import json
    import uuid

    fernet_key = get_secret_key()
    user_id = user["id"]
    updated_keys: list[str] = []

    if body.llm_provider is not None:
        set_user_secret(user_id, "llm_provider", str(body.llm_provider), fernet_key)
        updated_keys.append("llm_provider")

    if body.llm_model is not None:
        set_user_secret(user_id, "llm_model", str(body.llm_model), fernet_key)
        updated_keys.append("llm_model")

    if body.llm_council_enabled is not None:
        set_user_secret(user_id, "llm_council_enabled", str(body.llm_council_enabled), fernet_key)
        updated_keys.append("llm_council_enabled")

    for provider in body.llm_remove_providers:
        if provider in SUPPORTED_LLM_PROVIDERS:
            delete_user_secret(user_id, llm_secret_key(provider))
            updated_keys.append(f"remove:{provider}")

    provider_updates = {
        "claude": body.llm_api_key_claude,
        "openai": body.llm_api_key_openai,
        "gemini": body.llm_api_key_gemini,
    }
    for provider, value in provider_updates.items():
        if value is None:
            continue
        if value.strip():
            set_user_secret(user_id, llm_secret_key(provider), value.strip(), fernet_key)
            updated_keys.append(llm_secret_key(provider))
        else:
            delete_user_secret(user_id, llm_secret_key(provider))
            updated_keys.append(f"remove:{provider}")

    if body.llm_api_key is not None:
        if body.llm_api_key.strip():
            provider = _legacy_provider(body)
            set_user_secret(user_id, llm_secret_key(provider), body.llm_api_key.strip(), fernet_key)
            updated_keys.append(llm_secret_key(provider))
        else:
            requested = (body.llm_provider or "").strip().lower()
            if requested in SUPPORTED_LLM_PROVIDERS:
                delete_user_secret(user_id, llm_secret_key(requested))
                updated_keys.append(f"remove:{requested}")
            else:
                updated_keys.extend(_clear_personal_llm_keys(user_id))
        delete_user_secret(user_id, "llm_api_key")

    for key, value in {
        "tavily_api_key": body.tavily_api_key,
        "github_token": body.github_token,
        "github_pat": body.github_pat,
        "eventbrite_token": body.eventbrite_token,
    }.items():
        if value is None:
            continue
        if str(value).strip():
            set_user_secret(user_id, key, str(value).strip(), fernet_key)
            updated_keys.append(key)
        else:
            delete_user_secret(user_id, key)
            updated_keys.append(f"remove:{key}")

    # Feature toggles
    for field in FEATURE_TOGGLE_FIELDS:
        value = getattr(body, field)
        if value is not None:
            set_user_secret(user_id, field, str(value), fernet_key)
            updated_keys.append(field)

    # Custom providers
    from web.deps import get_custom_providers_for_user

    custom_providers = get_custom_providers_for_user(user_id)

    # Add custom provider
    if body.llm_custom_provider_add:
        new_provider = {
            "id": str(uuid.uuid4()),
            "display_name": body.llm_custom_provider_add.display_name.strip(),
            "base_url": body.llm_custom_provider_add.base_url.strip(),
            "api_key": body.llm_custom_provider_add.api_key.strip(),
            "model": body.llm_custom_provider_add.model.strip(),
        }
        # Validate base_url
        if not new_provider["base_url"].startswith(("http://", "https://")):
            raise HTTPException(
                status_code=400, detail="Base URL must start with http:// or https://"
            )
        custom_providers.append(new_provider)
        set_user_secret(user_id, "llm_custom_providers", json.dumps(custom_providers), fernet_key)
        updated_keys.append("llm_custom_provider_add")

    # Update custom provider
    if body.llm_custom_provider_update:
        provider_id = body.llm_custom_provider_update.id
        found = False
        for i, cp in enumerate(custom_providers):
            if cp["id"] == provider_id:
                found = True
                if body.llm_custom_provider_update.display_name:
                    cp["display_name"] = body.llm_custom_provider_update.display_name.strip()
                if body.llm_custom_provider_update.base_url:
                    url = body.llm_custom_provider_update.base_url.strip()
                    if not url.startswith(("http://", "https://")):
                        raise HTTPException(
                            status_code=400, detail="Base URL must start with http:// or https://"
                        )
                    cp["base_url"] = url
                if body.llm_custom_provider_update.api_key:
                    cp["api_key"] = body.llm_custom_provider_update.api_key.strip()
                if body.llm_custom_provider_update.model:
                    cp["model"] = body.llm_custom_provider_update.model.strip()
                custom_providers[i] = cp
                break
        if not found:
            raise HTTPException(status_code=404, detail="Custom provider not found")
        set_user_secret(user_id, "llm_custom_providers", json.dumps(custom_providers), fernet_key)
        updated_keys.append("llm_custom_provider_update")

    # Remove custom providers
    if body.llm_custom_providers_remove:
        custom_providers = [
            cp for cp in custom_providers if cp["id"] not in body.llm_custom_providers_remove
        ]
        if custom_providers:
            set_user_secret(
                user_id, "llm_custom_providers", json.dumps(custom_providers), fernet_key
            )
        else:
            delete_user_secret(user_id, "llm_custom_providers")
        updated_keys.extend([f"remove:custom:{pid}" for pid in body.llm_custom_providers_remove])

    logger.info("settings.updated", user_id=user_id, keys=updated_keys)
    return SettingsResponse(**get_settings_mask_for_user(user["id"]))


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage(
    days: int = Query(30, ge=1, le=365),
    user: dict = Depends(get_current_user),
):
    """Per-user LLM cost estimation from chat_query events."""
    stats = get_user_usage_stats(user["id"], days=days)
    return UsageStatsResponse(**stats)


@router.post("/test-llm")
async def test_llm_connectivity(
    provider: str | None = Query(None),
    user: dict = Depends(get_current_user),
):
    """Test that the stored LLM API key works with a minimal call."""
    fernet_key = get_secret_key()
    requested_provider = (provider or "").strip().lower() or None
    if requested_provider and requested_provider not in SUPPORTED_LLM_PROVIDERS:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    if requested_provider:
        api_key = _get_stored_provider_key(user["id"], requested_provider, fernet_key)
        provider_name = requested_provider
    else:
        provider_name, api_key, _source = resolve_llm_credentials_for_user(user["id"])

    if not api_key:
        raise HTTPException(status_code=400, detail="No API key configured")

    try:
        from llm import create_llm_provider

        provider = create_llm_provider(provider=provider_name, api_key=api_key)
        response = await asyncio.to_thread(
            provider.generate,
            messages=[{"role": "user", "content": "ping"}],
            system="Reply with exactly: ok",
            max_tokens=5,
        )
        return {"ok": True, "provider": provider.provider_name, "response": response.strip()}
    except Exception as e:
        logger.warning("settings.test_llm_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/test-custom-provider")
async def test_custom_provider(
    provider_id: str = Query(...),
    user: dict = Depends(get_current_user),
):
    """Test that a custom provider configuration works."""
    from llm.providers.openai_compatible import OpenAICompatibleProvider
    from web.deps import get_custom_providers_for_user

    custom_providers = get_custom_providers_for_user(user["id"])
    provider_config = next((cp for cp in custom_providers if cp["id"] == provider_id), None)

    if not provider_config:
        raise HTTPException(status_code=404, detail="Custom provider not found")

    try:
        provider = OpenAICompatibleProvider(
            base_url=provider_config["base_url"],
            api_key=provider_config["api_key"],
            model=provider_config["model"],
            display_name=provider_config["display_name"],
        )
        response = await asyncio.to_thread(
            provider.generate,
            messages=[{"role": "user", "content": "ping"}],
            system="Reply with exactly: ok",
            max_tokens=5,
        )
        return {
            "ok": True,
            "provider": provider_config["display_name"],
            "response": response.strip(),
        }
    except Exception as e:
        logger.warning(
            "settings.test_custom_provider_failed",
            user_id=user["id"],
            provider_id=provider_id,
            error=str(e),
        )
        raise HTTPException(status_code=422, detail=str(e))
