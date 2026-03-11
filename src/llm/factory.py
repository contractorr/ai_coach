"""LLM provider factory with auto-detection."""

import os

from .base import LLMError, LLMProvider

_PROVIDER_ENV_KEYS = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}

_AUTO_DETECT_ORDER = ["claude", "openai", "gemini"]

_CHEAP_MODELS = {
    "claude": "claude-haiku-4-5",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
}


def create_cheap_provider(
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    client=None,
) -> LLMProvider:
    """Create a cheap-tier provider for background/critic calls."""
    resolved = provider or "auto"
    if resolved == "auto":
        resolved = _auto_detect_provider(api_key)
    cheap_model = model or _CHEAP_MODELS.get(resolved)
    return create_llm_provider(provider=resolved, api_key=api_key, model=cheap_model, client=client)


def create_llm_provider(
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    client=None,
    extended_thinking: bool = False,
) -> LLMProvider:
    """Create an LLM provider instance.

    Args:
        provider: "claude", "openai", "gemini", "auto", or None (auto-detect)
        api_key: Explicit API key (overrides env var)
        model: Model name (None = provider default)
        client: Pre-built SDK client for testing/DI
        extended_thinking: Enable extended thinking support (Claude only)

    Returns:
        LLMProvider instance
    """
    resolved = provider or "auto"

    if resolved == "auto":
        resolved = _auto_detect_provider(api_key)

    if not api_key and not client:
        env_var = _PROVIDER_ENV_KEYS.get(resolved)
        if env_var:
            api_key = os.getenv(env_var)

    if resolved == "claude":
        from .providers.claude import ClaudeProvider

        return ClaudeProvider(
            api_key=api_key, model=model, client=client, extended_thinking=extended_thinking
        )
    elif resolved == "openai":
        from .providers.openai import OpenAIProvider

        return OpenAIProvider(api_key=api_key, model=model, client=client)
    elif resolved == "gemini":
        from .providers.gemini import GeminiProvider

        return GeminiProvider(api_key=api_key, model=model, client=client)
    else:
        raise LLMError(f"Unknown provider: {resolved}. Use: claude, openai, gemini")


def _detect_provider_from_key(api_key: str) -> str | None:
    """Infer provider from API key prefix."""
    if api_key.startswith("sk-ant-"):
        return "claude"
    if api_key.startswith("sk-"):
        return "openai"
    if api_key.startswith("AI"):
        return "gemini"
    return None


def _auto_detect_provider(api_key: str | None = None) -> str:
    """Detect provider from explicit key prefix, then env vars."""
    if api_key:
        inferred = _detect_provider_from_key(api_key)
        if inferred:
            return inferred
        raise LLMError(
            "Could not infer provider from explicit API key. Pass provider=claude, openai, or gemini."
        )

    for name in _AUTO_DETECT_ORDER:
        env_var = _PROVIDER_ENV_KEYS[name]
        if os.getenv(env_var):
            return name
    raise LLMError(
        "No LLM API key found. Set one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY"
    )
