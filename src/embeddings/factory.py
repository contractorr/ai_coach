"""Embedding provider factory with auto-detection."""

from __future__ import annotations

import os

import structlog

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
    dimensions = dimensions or emb_config.get("dimensions")

    if resolved == "auto":
        resolved = _auto_detect_provider()

    if resolved == "hash":
        from chroma_utils import SimpleHashEmbeddingFunction

        return SimpleHashEmbeddingFunction(dimensions=dimensions or 256)

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

    # Unknown provider — fall back to hash
    logger.warning("unknown_embedding_provider", provider=resolved)
    from chroma_utils import SimpleHashEmbeddingFunction

    return SimpleHashEmbeddingFunction()


def _auto_detect_provider() -> str:
    """Detect best available embedding provider from env vars."""
    for name in _AUTO_DETECT_ORDER:
        if os.getenv(_PROVIDER_ENV_KEYS[name]):
            logger.debug("embedding_provider_detected", provider=name)
            return name
    return "hash"
