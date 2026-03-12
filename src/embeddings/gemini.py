"""Gemini embedding provider."""

from __future__ import annotations

from typing import Iterable

import structlog

from .base import EmbeddingFunction

logger = structlog.get_logger()

_BATCH_LIMIT = 100  # Gemini API max texts per request


class GeminiEmbeddingFunction(EmbeddingFunction):
    """Embedding via Google Gemini ``embed_content`` API (google.genai SDK)."""

    provider_name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-embedding-2-preview",
        dimensions: int = 768,
    ):
        import os

        from google import genai

        key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        self._client = genai.Client(api_key=key)
        self._model = model
        self.dimensions = dimensions

    def __call__(self, input: Iterable[str]) -> list[list[float]]:
        texts = list(input)
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), _BATCH_LIMIT):
            batch = texts[i : i + _BATCH_LIMIT]
            result = self._client.models.embed_content(
                model=self._model,
                contents=batch,
                config={"output_dimensionality": self.dimensions},
            )
            for emb in result.embeddings:
                all_embeddings.append(list(emb.values))

        return all_embeddings
