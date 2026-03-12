"""OpenAI embedding provider."""

from __future__ import annotations

from typing import Iterable

import structlog

from .base import EmbeddingFunction

logger = structlog.get_logger()


class OpenAIEmbeddingFunction(EmbeddingFunction):
    """Embedding via OpenAI ``embeddings.create`` API."""

    provider_name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ):
        import os

        from openai import OpenAI

        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._client = OpenAI(api_key=key)
        self._model = model
        self.dimensions = dimensions

    def __call__(self, input: Iterable[str]) -> list[list[float]]:
        texts = list(input)
        if not texts:
            return []

        response = self._client.embeddings.create(
            model=self._model,
            input=texts,
            dimensions=self.dimensions,
        )
        return [item.embedding for item in response.data]
