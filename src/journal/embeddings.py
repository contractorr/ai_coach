"""Vector embedding operations using ChromaDB."""

from pathlib import Path
from typing import Optional

import structlog

from chroma_utils import LocalCollection, build_embedding_function

logger = structlog.get_logger()

# Default embedding model used by ChromaDB
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class EmbeddingManager:
    """Manages vector embeddings for journal entries."""

    def __init__(self, chroma_dir: str | Path, collection_name: str = "journal"):
        self.chroma_dir = Path(chroma_dir).expanduser()
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedding_function = build_embedding_function()

        self.collection = LocalCollection(
            base_dir=self.chroma_dir,
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine", "embedding_model": DEFAULT_EMBEDDING_MODEL},
        )

    def add_entry(
        self,
        entry_id: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Add or update entry embedding."""
        # Sanitize metadata - ChromaDB only accepts str, int, float, bool, None
        clean_meta = {}
        if metadata:
            for k, v in metadata.items():
                if isinstance(v, list):
                    clean_meta[k] = ",".join(str(x) for x in v) if v else ""
                elif isinstance(v, (str, int, float, bool)) or v is None:
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)

        # ChromaDB requires non-empty metadata or None
        self.collection.upsert(
            ids=[entry_id],
            documents=[content],
            metadatas=[clean_meta] if clean_meta else None,
        )

    def remove_entry(self, entry_id: str) -> None:
        """Remove entry from vector store."""
        try:
            self.collection.delete(ids=[entry_id])
        except Exception as e:
            logger.warning("embedding_remove_failed", entry_id=entry_id, error=str(e))

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """Query similar entries.

        Args:
            query_text: Search query
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            List of matching entries with scores
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        entries = []
        if results["ids"] and results["ids"][0]:
            for i, entry_id in enumerate(results["ids"][0]):
                entries.append(
                    {
                        "id": entry_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                    }
                )

        return entries

    def sync_from_storage(self, entries: list[dict]) -> tuple[int, int]:
        """Sync embeddings from storage entries.

        Args:
            entries: List of dicts with id, content, metadata

        Returns:
            Tuple of (added, removed) counts
        """
        # Get existing IDs
        existing = set()
        try:
            existing_data = self.collection.get()
            existing = set(existing_data["ids"]) if existing_data["ids"] else set()
        except Exception as e:
            logger.warning(
                "chroma_get_existing_failed", collection=self.collection_name, error=str(e)
            )

        current_ids = {e["id"] for e in entries}

        # Add/update entries
        added = 0
        for entry in entries:
            self.add_entry(entry["id"], entry["content"], entry.get("metadata"))
            if entry["id"] not in existing:
                added += 1

        # Remove deleted entries
        removed = 0
        for old_id in existing - current_ids:
            self.remove_entry(old_id)
            removed += 1

        return added, removed

    def count(self) -> int:
        """Get total number of embedded entries."""
        return self.collection.count()

    def health_check(self) -> dict:
        """Return health info for this collection."""
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
        self.collection.delete_collection()
        self.collection = LocalCollection(
            base_dir=self.chroma_dir,
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine", "embedding_model": DEFAULT_EMBEDDING_MODEL},
        )
