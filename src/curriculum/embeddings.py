"""ChromaDB embeddings for cross-guide chapter connections."""

from pathlib import Path
from typing import Callable

import structlog

from journal.embeddings import EmbeddingManager

logger = structlog.get_logger()


class ChapterEmbeddingManager:
    """Manages chapter embeddings for cross-guide similarity search."""

    def __init__(self, chroma_dir: str | Path, config: dict | None = None):
        self._emb = EmbeddingManager(
            chroma_dir=chroma_dir,
            base_name="curriculum_chapters",
            config=config,
        )

    @property
    def is_available(self) -> bool:
        """Whether semantic embeddings are available."""
        return self._emb.is_available

    def upsert_chapter(
        self,
        chapter_id: str,
        content: str,
        guide_id: str,
        chapter_title: str,
        content_hash: str,
    ) -> None:
        """Add or update a chapter embedding."""
        if not self.is_available:
            return
        # Truncate to ~2000 words
        words = content.split()
        if len(words) > 2000:
            content = " ".join(words[:2000])

        self._emb.add_entry(
            entry_id=chapter_id,
            content=content,
            metadata={
                "guide_id": guide_id,
                "title": chapter_title,
                "content_hash": content_hash,
            },
        )

    def find_related(
        self,
        chapter_content: str,
        current_guide_id: str,
        enrolled_guide_ids: list[str],
        n_results: int = 3,
    ) -> list[dict]:
        """Find related chapters from other enrolled guides."""
        if not self.is_available:
            return []
        # Query more than needed so we can post-filter
        raw = self._emb.query(
            query_text=chapter_content[:3000],
            n_results=n_results * 4,
        )

        results = []
        for r in raw:
            meta = r.get("metadata", {})
            gid = meta.get("guide_id", "")
            # Exclude same guide
            if gid == current_guide_id:
                continue
            # Only enrolled guides
            if gid not in enrolled_guide_ids:
                continue
            # Distance threshold (higher for hash-based fallback embedder)
            if r.get("distance", 1.0) > 0.5:
                continue
            results.append(
                {
                    "chapter_id": r["id"],
                    "guide_id": gid,
                    "title": meta.get("title", ""),
                    "distance": r.get("distance", 0),
                }
            )
            if len(results) >= n_results:
                break

        return results

    def sync_from_chapters(
        self,
        chapters: list[dict],
        content_reader: Callable[[str], str | None],
    ) -> int:
        """Bulk upsert chapters. Skips glossary chapters."""
        if not self.is_available:
            return 0
        count = 0
        for ch in chapters:
            if ch.get("is_glossary"):
                continue
            content = content_reader(ch["id"])
            if not content:
                continue
            self.upsert_chapter(
                chapter_id=ch["id"],
                content=content,
                guide_id=ch["guide_id"],
                chapter_title=ch.get("title", ""),
                content_hash=ch.get("content_hash", ""),
            )
            count += 1
        return count

    def count(self) -> int:
        if not self.is_available:
            return 0
        return self._emb.count()
