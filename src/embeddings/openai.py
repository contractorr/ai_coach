"""OpenAI embedding provider."""

from __future__ import annotations

from typing import Iterable

from .base import EmbeddingFunction

_BATCH_LIMIT = 2048  # OpenAI practical max texts per request


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
        if not key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIEmbeddingFunction")
        self._client = OpenAI(api_key=key)
        self._model = model
        self.dimensions = dimensions

    def __call__(self, input: Iterable[str]) -> list[list[float]]:
        texts = list(input)
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), _BATCH_LIMIT):
            batch = texts[i : i + _BATCH_LIMIT]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
                dimensions=self.dimensions,
            )
            all_embeddings.extend(item.embedding for item in response.data)
        return all_embeddings
