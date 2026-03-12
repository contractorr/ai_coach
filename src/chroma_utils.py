"""ChromaDB helpers, including a deterministic local embedding fallback."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_+\-.#]+", (text or "").lower())


class SimpleHashEmbeddingFunction:
    """Deterministic lexical embedding fallback when ONNX runtime is unavailable."""

    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    def _embed_text(self, text: str) -> list[float]:
        counts = Counter(_tokenize(text))
        vector = [0.0] * self.dimensions
        if not counts:
            return vector

        for token, weight in counts.items():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign * float(weight)

        norm = math.sqrt(sum(value * value for value in vector))
        if norm > 0:
            vector = [value / norm for value in vector]
        return vector

    def __call__(self, input: Iterable[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in input]

    @staticmethod
    def name() -> str:
        return "simple-hash-fallback"


def build_embedding_function(config: dict | None = None):
    """Return the configured embedding function.

    Delegates to the pluggable embedding factory which auto-detects the best
    available provider (Gemini → OpenAI → hash fallback).
    """
    try:
        from embeddings import create_embedding_function

        return create_embedding_function(config=config)
    except Exception:
        return SimpleHashEmbeddingFunction()


class LocalCollection:
    """Small file-backed vector store compatible with the subset of Chroma we use."""

    def __init__(
        self,
        base_dir: str | Path,
        name: str,
        metadata: dict | None = None,
        embedding_function: SimpleHashEmbeddingFunction | None = None,
    ):
        self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.name = name
        self.metadata = metadata or {}
        self.embedding_function = embedding_function or SimpleHashEmbeddingFunction()
        self.path = self.base_dir / f"{name}.json"
        self._records = self._load()

    def _load(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8") or "{}")
        if not isinstance(data, dict):
            return {}
        return data

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._records), encoding="utf-8")

    def upsert(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> None:
        metadata_list = metadatas or [{} for _ in ids]
        vectors = self.embedding_function(documents)
        for item_id, document, meta, vector in zip(
            ids, documents, metadata_list, vectors, strict=True
        ):
            self._records[str(item_id)] = {
                "document": document,
                "metadata": meta or {},
                "vector": vector,
            }
        self._save()

    def delete(self, *, ids: list[str]) -> None:
        for item_id in ids:
            self._records.pop(str(item_id), None)
        self._save()

    def count(self) -> int:
        return len(self._records)

    def get(self, *, ids: list[str] | None = None, include: list[str] | None = None) -> dict:
        requested_ids = (
            [str(item_id) for item_id in ids] if ids is not None else list(self._records.keys())
        )
        record_ids = [item_id for item_id in requested_ids if item_id in self._records]
        include = include or ["documents", "metadatas"]

        result = {"ids": record_ids}
        if "documents" in include:
            result["documents"] = [self._records[item_id]["document"] for item_id in record_ids]
        if "metadatas" in include:
            result["metadatas"] = [
                self._records[item_id].get("metadata", {}) for item_id in record_ids
            ]
        if "embeddings" in include:
            result["embeddings"] = [
                self._records[item_id].get("vector", []) for item_id in record_ids
            ]
        return result

    def query(
        self,
        *,
        query_texts: list[str] | None = None,
        query_embeddings: list[list[float]] | None = None,
        n_results: int,
        where: dict | None = None,
        include: list[str] | None = None,
    ) -> dict:
        include = include or ["documents", "metadatas", "distances"]
        ids_out: list[list[str]] = []
        documents_out: list[list[str]] = []
        metadatas_out: list[list[dict]] = []
        distances_out: list[list[float]] = []

        candidates = [
            (item_id, record)
            for item_id, record in self._records.items()
            if self._matches_where(record.get("metadata", {}), where)
        ]

        query_vectors = (
            query_embeddings
            if query_embeddings is not None
            else self.embedding_function(query_texts or [])
        )

        for query_vector in query_vectors:
            ranked = sorted(
                candidates,
                key=lambda item: self._cosine_distance(query_vector, item[1].get("vector", [])),
            )[:n_results]
            ids_out.append([item_id for item_id, _ in ranked])
            documents_out.append([record.get("document", "") for _, record in ranked])
            metadatas_out.append([record.get("metadata", {}) for _, record in ranked])
            distances_out.append(
                [
                    self._cosine_distance(query_vector, record.get("vector", []))
                    for _, record in ranked
                ]
            )

        return {
            "ids": ids_out,
            "documents": documents_out if "documents" in include else None,
            "metadatas": metadatas_out if "metadatas" in include else None,
            "distances": distances_out if "distances" in include else None,
        }

    @staticmethod
    def _matches_where(metadata: dict, where: dict | None) -> bool:
        if not where:
            return True
        for key, expected in where.items():
            if metadata.get(key) != expected:
                return False
        return True

    @staticmethod
    def _cosine_distance(left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 1.0
        dot = sum(a * b for a, b in zip(left, right, strict=False))
        return 1.0 - dot

    def delete_collection(self) -> None:
        self._records = {}
        if self.path.exists():
            self.path.unlink()
