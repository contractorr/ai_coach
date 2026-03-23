"""Vector embeddings for intelligence items using ChromaDB."""

from pathlib import Path
from typing import Optional

import structlog

from chroma_utils import LocalCollection, build_embedding_function
from embeddings.versioning import auto_migrate_collection, model_tag, versioned_name

logger = structlog.get_logger()


class IntelEmbeddingManager:
    """Manages vector embeddings for intelligence items."""

    def __init__(
        self,
        chroma_dir: str | Path,
        default_results: int = 5,
        similarity_threshold: float = 0.85,
        config: dict | None = None,
    ):
        self.chroma_dir = Path(chroma_dir).expanduser()
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.default_results = default_results
        self.similarity_threshold = similarity_threshold
        self.embedding_function = build_embedding_function(config=config)

        if self.embedding_function is None:
            logger.info("embeddings_disabled", component="intel")
            self.collection = None
            self.collection_name = None
            self._model_name = "none"
            return

        self.collection_name = versioned_name("intel", self.embedding_function)
        auto_migrate_collection(self.chroma_dir, "intel", self.collection_name)

        self._model_name = model_tag(self.embedding_function)
        self.collection = LocalCollection(
            base_dir=self.chroma_dir,
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine", "embedding_model": self._model_name},
        )

    @property
    def is_available(self) -> bool:
        """Whether semantic embeddings are available."""
        return self.collection is not None

    def add_item(
        self,
        item_id: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Add or update intel item embedding."""
        if not self.is_available:
            return
        self.collection.upsert(
            ids=[item_id],
            documents=[content],
            metadatas=[metadata or {}],
        )

    def add_items_batch(
        self,
        items: list[dict],
    ) -> int:
        """Add multiple items in batch.

        Args:
            items: List of dicts with id, content, metadata keys

        Returns:
            Number of items added
        """
        if not self.is_available:
            return 0
        if not items:
            return 0

        ids = [item["id"] for item in items]
        documents = [item["content"] for item in items]
        metadatas = [item.get("metadata", {}) for item in items]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        return len(items)

    def remove_item(self, item_id: str) -> None:
        """Remove item from vector store."""
        if not self.is_available:
            return
        try:
            self.collection.delete(ids=[item_id])
        except Exception as e:
            logger.warning("intel_embedding_remove_failed", item_id=item_id, error=str(e))

    def query(
        self,
        query_text: str,
        n_results: int = 10,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """Query similar intel items.

        Args:
            query_text: Search query
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            List of matching items with scores
        """
        if not self.is_available:
            return []
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        items = []
        if results["ids"] and results["ids"][0]:
            for i, item_id in enumerate(results["ids"][0]):
                items.append(
                    {
                        "id": item_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                    }
                )

        return items

    def sync_from_storage(self, items: list[dict]) -> tuple[int, int]:
        """Sync embeddings from intel storage items.

        Args:
            items: List of dicts with id, content, metadata

        Returns:
            Tuple of (added, removed) counts
        """
        if not self.is_available:
            return (0, 0)
        existing = set()
        try:
            existing_data = self.collection.get()
            existing = set(existing_data["ids"]) if existing_data["ids"] else set()
        except Exception as e:
            logger.warning(
                "chroma_get_existing_failed", collection=self.collection_name, error=str(e)
            )

        current_ids = {str(item["id"]) for item in items}

        # Add/update items
        added = 0
        for item in items:
            item_id = str(item["id"])
            self.add_item(item_id, item["content"], item.get("metadata"))
            if item_id not in existing:
                added += 1

        # Remove deleted items
        removed = 0
        for old_id in existing - current_ids:
            self.remove_item(old_id)
            removed += 1

        return added, removed

    def count(self) -> int:
        """Get total number of embedded items."""
        if not self.is_available:
            return 0
        return self.collection.count()

    def health_check(self) -> dict:
        """Return health info for this collection."""
        if not self.is_available:
            return {
                "status": "disabled",
                "count": 0,
                "collection_name": self.collection_name,
                "model": "none",
            }
        try:
            count = self.collection.count()
            meta = self.collection.metadata or {}
            return {
                "status": "ok",
                "count": count,
                "collection_name": self.collection_name,
                "model": meta.get("embedding_model", "unknown"),
            }
        except Exception as e:
            return {
                "status": "error",
                "count": 0,
                "collection_name": self.collection_name,
                "model": "unknown",
                "error": str(e),
            }

    def delete_collection(self) -> None:
        """Delete and reinitialize the collection."""
        if not self.is_available:
            return
        self.collection.delete_collection()
        self.collection = LocalCollection(
            base_dir=self.chroma_dir,
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine", "embedding_model": self._model_name},
        )

    def find_similar(
        self, text: str, threshold: float | None = None, where: dict | None = None
    ) -> str | None:
        """Check if similar content exists.

        Args:
            text: Content to check
            threshold: Similarity threshold (0-1, higher = more similar)
            where: Optional Chroma metadata filter (e.g. time-window)

        Returns:
            Chroma doc ID of the canonical match, or None. Truthiness preserved.
        """
        if not self.is_available:
            return None
        threshold = threshold if threshold is not None else self.similarity_threshold
        if self.collection.count() == 0:
            return None

        kwargs: dict = {"query_texts": [text], "n_results": 1, "include": ["distances"]}
        if where is not None:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        if results["distances"] and results["distances"][0]:
            # ChromaDB returns cosine distance, convert to similarity
            distance = results["distances"][0][0]
            similarity = 1 - distance
            if similarity >= threshold and results["ids"] and results["ids"][0]:
                return results["ids"][0][0]

        return None
