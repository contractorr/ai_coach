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
from web.models import SettingsResponse, SettingsUpdate
from web.user_store import delete_user_secret, get_user_secret, set_user_secret

logger = structlog.get_logger()

router = APIRouter(prefix="/api/settings", tags=["settings"])


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


def _get_stored_provider_key(user_id: str, provider: str, fernet_key: str) -> str | None:
    provider_key = get_user_secret(user_id, llm_secret_key(provider), fernet_key)
    if provider_key:
        return provider_key

    legacy_key = get_user_secret(user_id, "llm_api_key", fernet_key)
    legacy_provider = get_user_secret(user_id, "llm_provider", fernet_key)
    if legacy_key and legacy_provider == provider:
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
        provider = _legacy_provider(body)
        if body.llm_api_key.strip():
            set_user_secret(user_id, llm_secret_key(provider), body.llm_api_key.strip(), fernet_key)
            updated_keys.append(llm_secret_key(provider))
        else:
            delete_user_secret(user_id, llm_secret_key(provider))
            updated_keys.append(f"remove:{provider}")
        delete_user_secret(user_id, "llm_api_key")

    for key, value in {
        "tavily_api_key": body.tavily_api_key,
        "github_token": body.github_token,
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

    logger.info("settings.updated", user_id=user_id, keys=updated_keys)
    return SettingsResponse(**get_settings_mask_for_user(user["id"]))


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
