"""Embedding provider factory with auto-detection."""

from __future__ import annotations

import os

import structlog

from observability import metrics

logger = structlog.get_logger()

_PROVIDER_ENV_KEYS = {
    "gemini": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
}

_AUTO_DETECT_ORDER = ["gemini", "openai"]


def create_embedding_function(
    provider: str | None = None,
    model: str | None = None,
    dimensions: int | None = None,
    config: dict | None = None,
):
    """Create an embedding function instance.

    Args:
        provider: "gemini", "openai", "hash", "auto", or None (auto-detect)
        model: Model name override
        dimensions: Embedding dimensions override
        config: Full app config dict — reads ``embeddings.*`` keys

    Returns:
        Callable matching ``__call__(Iterable[str]) -> list[list[float]]``
    """
    emb_config = (config or {}).get("embeddings", {})
    resolved = provider or emb_config.get("provider") or "auto"
    model = model or emb_config.get("model")
    dimensions = dimensions if dimensions is not None else emb_config.get("dimensions")

    # Track whether hash was explicitly configured vs auto-detected
    explicitly_configured = provider or emb_config.get("provider")

    if resolved == "auto":
        resolved = _auto_detect_provider()

    if resolved == "hash":
        if explicitly_configured == "hash":
            # User opted in explicitly
            from chroma_utils import SimpleHashEmbeddingFunction

            logger.warning("embedding_using_explicit_hash", reason="user configured provider=hash")
            return SimpleHashEmbeddingFunction(dimensions=dimensions or 256)
        # Auto-detected: no real provider available — return None
        logger.warning(
            "embedding_no_provider",
            hint="set GOOGLE_API_KEY or OPENAI_API_KEY for semantic search",
        )
        metrics.counter("embedding.no_provider")
        return None

    if resolved == "gemini":
        from .gemini import GeminiEmbeddingFunction

        kwargs: dict = {}
        if model:
            kwargs["model"] = model
        if dimensions:
            kwargs["dimensions"] = dimensions
        return GeminiEmbeddingFunction(**kwargs)

    if resolved == "openai":
        from .openai import OpenAIEmbeddingFunction

        kwargs = {}
        if model:
            kwargs["model"] = model
        if dimensions:
            kwargs["dimensions"] = dimensions
        return OpenAIEmbeddingFunction(**kwargs)

    # Unknown provider — return None
    logger.warning("unknown_embedding_provider", provider=resolved)
    metrics.counter("embedding.no_provider")
    return None


def _auto_detect_provider() -> str:
    """Detect best available embedding provider from env vars."""
    for name in _AUTO_DETECT_ORDER:
        if os.getenv(_PROVIDER_ENV_KEYS[name]):
            logger.debug("embedding_provider_detected", provider=name)
            return name
    return "hash"
