"""Semantic search across journal entries."""

from pathlib import Path
from typing import Optional

import frontmatter

from .embeddings import EmbeddingManager
from .fts import JournalFTSIndex
from .storage import JournalStorage


class JournalSearch:
    """Unified search interface combining semantic and keyword search."""

    def __init__(
        self,
        storage: JournalStorage,
        embeddings: EmbeddingManager,
        fts_index: Optional[JournalFTSIndex] = None,
    ):
        self.storage = storage
        self.embeddings = embeddings
        self.fts = fts_index

    def semantic_search(
        self,
        query: str,
        n_results: int = 5,
        entry_type: Optional[str] = None,
    ) -> list[dict]:
        """Search using semantic similarity.

        Args:
            query: Natural language query
            n_results: Max results to return
            entry_type: Optional filter by entry type

        Returns:
            List of matching entries with relevance scores
        """
        # Fall back to keyword search if no embeddings
        if self.embeddings is None:
            return self.keyword_search(query, limit=n_results, entry_type=entry_type)

        where = {"type": entry_type} if entry_type else None
        results = self.embeddings.query(query, n_results=n_results, where=where)

        # Enrich with full entry data
        enriched = []
        for r in results:
            try:
                path = Path(r["id"])
                if path.exists():
                    post = frontmatter.load(path)
                    enriched.append(
                        {
                            "path": path,
                            "title": post.get("title", path.stem),
                            "type": post.get("type"),
                            "created": post.get("created"),
                            "tags": post.get("tags", []),
                            "content": post.content,
                            "relevance": 1 - r["distance"],  # Convert distance to similarity
                        }
                    )
            except (OSError, ValueError):
                continue

        return enriched

    def keyword_search(
        self,
        keyword: str,
        entry_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """Keyword search — delegates to FTS5 when available, else in-memory scan."""
        if self.fts:
            return self._keyword_search_fts(keyword, entry_type=entry_type, limit=limit)
        return self._keyword_search_fallback(keyword, entry_type=entry_type, limit=limit)

    def _keyword_search_fts(
        self,
        keyword: str,
        entry_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """FTS5-backed keyword search with BM25 ranking."""
        rows = self.fts.search(keyword, limit=limit, entry_type=entry_type)
        results = []
        for row in rows:
            try:
                path = Path(row["path"])
                if not path.exists():
                    continue
                post = frontmatter.load(path)
                results.append(
                    {
                        "path": path,
                        "title": post.get("title", path.stem),
                        "type": post.get("type"),
                        "created": post.get("created"),
                        "tags": post.get("tags", []),
                        "content": post.content,
                        "relevance": -row["rank"],  # bm25() returns negative; negate for ranking
                    }
                )
            except (OSError, ValueError):
                continue
        return results

    def _keyword_search_fallback(
        self,
        keyword: str,
        entry_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """In-memory keyword scan (legacy fallback)."""
        matches = []

        terms = [t.lower() for t in keyword.lower().split() if t]

        for path in sorted(self.storage.journal_dir.glob("*.md"), reverse=True):
            try:
                post = frontmatter.load(path)
                if entry_type and post.get("type") != entry_type:
                    continue
                content_lower = (post.content or "").lower()
                count = sum(content_lower.count(t) for t in terms)
                if count > 0:
                    matches.append(
                        {
                            "path": path,
                            "title": post.get("title", path.stem),
                            "type": post.get("type"),
                            "created": post.get("created"),
                            "tags": post.get("tags", []),
                            "content": post.content,
                            "relevance": count,
                        }
                    )
            except (OSError, ValueError):
                continue

        matches.sort(key=lambda m: m["relevance"], reverse=True)
        return matches[:limit]

    def hybrid_search(
        self,
        query: str,
        n_results: int = 5,
        semantic_weight: float = 0.7,
        entry_type: Optional[str] = None,
    ) -> list[dict]:
        """Combine semantic + keyword search with reciprocal rank fusion."""
        semantic_results = self.semantic_search(
            query, n_results=n_results * 2, entry_type=entry_type
        )
        keyword_results = self.keyword_search(query, entry_type=entry_type, limit=n_results * 2)

        scores: dict[str, float] = {}
        items: dict[str, dict] = {}

        for i, item in enumerate(semantic_results):
            key = str(item["path"])
            scores[key] = scores.get(key, 0) + (1.0 / (i + 1)) * semantic_weight
            items[key] = item

        for i, item in enumerate(keyword_results):
            key = str(item["path"])
            scores[key] = scores.get(key, 0) + (1.0 / (i + 1)) * (1 - semantic_weight)
            if key not in items:
                items[key] = item

        sorted_keys = sorted(scores, key=lambda k: scores[k], reverse=True)
        return [items[k] for k in sorted_keys[:n_results]]

    def get_context_for_query(
        self,
        query: str,
        max_entries: int = 5,
        max_chars: int = 8000,
    ) -> str:
        """Get relevant journal context for RAG.

        Args:
            query: User question/query
            max_entries: Max entries to include
            max_chars: Max total characters

        Returns:
            Formatted context string for LLM
        """
        results = self.hybrid_search(query, n_results=max_entries)

        if not results:
            return "No relevant journal entries found."

        context_parts = []
        total_chars = 0

        for r in results:
            entry_text = f"""
--- Entry: {r["title"]} ({r["type"]}) ---
Date: {r["created"]}
Tags: {", ".join(r["tags"]) if r["tags"] else "none"}

{r["content"]}
"""
            if total_chars + len(entry_text) > max_chars:
                # Truncate last entry if needed
                remaining = max_chars - total_chars
                if remaining > 200:
                    context_parts.append(entry_text[:remaining] + "...[truncated]")
                break

            context_parts.append(entry_text)
            total_chars += len(entry_text)

        return "\n".join(context_parts)

    def sync_embeddings(self) -> tuple[int, int]:
        """Sync all journal entries to embedding store (and FTS index if present)."""
        entries = self.storage.get_all_content()
        if self.fts:
            self.fts.sync_from_storage(entries)
        return self.embeddings.sync_from_storage(entries)
