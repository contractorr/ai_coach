"""Abstract base for embedding providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


class EmbeddingFunction(ABC):
    """Base class for all embedding providers.

    Contract: ``__call__(Iterable[str]) -> list[list[float]]``
    This matches what ``LocalCollection`` expects.

    Subclasses must set ``provider_name`` (str) and ``dimensions`` (int)
    as class attributes or in ``__init__``.
    """

    provider_name: str
    dimensions: int

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Validate provider_name is declared at the class level (dimensions may be set in __init__)
        if not getattr(cls, "__abstractmethods__", None) and "provider_name" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define class attribute 'provider_name'")

    @abstractmethod
    def __call__(self, input: Iterable[str]) -> list[list[float]]: ...

    def name(self) -> str:
        return self.provider_name
