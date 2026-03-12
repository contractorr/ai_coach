"""Abstract base for embedding providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


class EmbeddingFunction(ABC):
    """Base class for all embedding providers.

    Contract: ``__call__(Iterable[str]) -> list[list[float]]``
    This matches what ``LocalCollection`` expects.
    """

    provider_name: str
    dimensions: int

    @abstractmethod
    def __call__(self, input: Iterable[str]) -> list[list[float]]: ...

    def name(self) -> str:
        return self.provider_name
