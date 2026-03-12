"""Vector embedding operations for Library items using ChromaDB."""

from pathlib import Path
from typing import Optional

import structlog

from chroma_utils import LocalCollection, build_embedding_function

logger = structlog.get_logger()


class LibraryEmbeddingManager:
    """Manages vector embeddings for library documents."""

    def __init__(
        self, chroma_dir: str | Path, collection_name: str = "library", config: dict | None = None
    ):
        self.chroma_dir = Path(chroma_dir).expanduser()
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedding_function = build_embedding_function(config=config)

        model_name = getattr(self.embedding_function, "name", lambda: "unknown")()
        self.collection = LocalCollection(
            base_dir=self.chroma_dir,
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine", "embedding_model": model_name},
        )

    def add_item(
        self,
        item_id: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Add or update a library item embedding."""
        clean_meta = {}
        if metadata:
            for k, v in metadata.items():
                if isinstance(v, list):
                    clean_meta[k] = ",".join(str(x) for x in v) if v else ""
                elif isinstance(v, (str, int, float, bool)) or v is None:
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)

        self.collection.upsert(
            ids=[item_id],
            documents=[content],
            metadatas=[clean_meta] if clean_meta else None,
        )

    def remove_item(self, item_id: str) -> None:
        """Remove item from vector store."""
        try:
            self.collection.delete(ids=[item_id])
        except Exception as e:
            logger.warning("library_embedding_remove_failed", item_id=item_id, error=str(e))

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """Query similar library items."""
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
        """Sync embeddings from storage items.

        Args:
            items: List of dicts with id, content, metadata

        Returns:
            Tuple of (added, removed) counts
        """
        existing = set()
        try:
            existing_data = self.collection.get()
            existing = set(existing_data["ids"]) if existing_data["ids"] else set()
        except Exception as e:
            logger.warning(
                "library_chroma_get_existing_failed",
                collection=self.collection_name,
                error=str(e),
            )

        current_ids = {item["id"] for item in items}

        added = 0
        for item in items:
            if item["id"] not in existing:
                self.add_item(item["id"], item["content"], item.get("metadata"))
                added += 1

        removed = 0
        for old_id in existing - current_ids:
            self.remove_item(old_id)
            removed += 1

        return added, removed

    def count(self) -> int:
        """Get total number of embedded items."""
        return self.collection.count()
