"""Semantic and keyword search for intelligence items."""

import re
import sqlite3
from pathlib import Path
from typing import Optional

import structlog

from db import wal_connect

from .embeddings import IntelEmbeddingManager
from .scraper import IntelStorage

logger = structlog.get_logger()


class ProfileTerms:
    """Structured profile terms for relevance scoring."""

    def __init__(
        self,
        skills: list[str] | None = None,
        tech: list[str] | None = None,
        interests: list[str] | None = None,
        goal_keywords: list[str] | None = None,
        project_keywords: list[str] | None = None,
    ):
        self.skills = _normalize_terms(skills or [])
        self.tech = _normalize_terms(tech or [])
        self.interests = _normalize_terms(interests or [])
        self.goal_keywords = _normalize_terms(goal_keywords or [])
        self.project_keywords = _normalize_terms(project_keywords or [])

    @property
    def is_empty(self) -> bool:
        return not any(
            [self.skills, self.tech, self.interests, self.goal_keywords, self.project_keywords]
        )

    @property
    def all_terms(self) -> set[str]:
        """All terms combined for broad matching."""
        return self.skills | self.tech | self.interests | self.goal_keywords | self.project_keywords


def _normalize_terms(terms: list[str]) -> set[str]:
    """Lowercase, strip, deduplicate, split multi-word terms into individual words too."""
    result = set()
    for t in terms:
        t = t.lower().strip()
        if not t:
            continue
        result.add(t)
        # Also add individual words for multi-word terms (e.g., "machine learning" → "machine", "learning")
        words = t.split()
        if len(words) > 1:
            for w in words:
                if len(w) > 2:  # skip tiny words like "of", "ai" handled by full term
                    result.add(w)
    return result


def load_profile_terms(profile_path: str | Path) -> "ProfileTerms":
    """Load user profile and build ProfileTerms for relevance scoring.

    Standalone version of RAGRetriever._load_profile_terms.
    """
    _GOAL_STOPWORDS = {
        "the",
        "and",
        "for",
        "that",
        "with",
        "this",
        "from",
        "have",
        "will",
        "are",
        "was",
        "been",
        "being",
        "would",
        "could",
        "should",
        "into",
        "about",
        "more",
        "some",
        "than",
        "also",
        "just",
        "over",
        "such",
        "want",
        "like",
        "get",
        "make",
        "see",
        "know",
        "take",
        "next",
        "year",
        "years",
        "month",
        "months",
        "within",
        "achieve",
    }
    try:
        from profile.storage import ProfileStorage

        ps = ProfileStorage(str(profile_path))
        profile = ps.load()
        if not profile:
            return ProfileTerms()

        goal_keywords: list[str] = []
        for text in [profile.goals_short_term, profile.goals_long_term, profile.aspirations]:
            if text:
                words = re.findall(r"[a-z][a-z0-9\-]+", text.lower())
                goal_keywords.extend(w for w in words if len(w) > 2 and w not in _GOAL_STOPWORDS)

        project_keywords: list[str] = []
        for p in profile.active_projects:
            words = re.findall(r"[a-z][a-z0-9\-]+", p.lower())
            project_keywords.extend(w for w in words if len(w) > 2)

        return ProfileTerms(
            skills=[s.name for s in profile.skills],
            tech=profile.languages_frameworks + profile.technologies_watching,
            interests=profile.interests + profile.industries_watching,
            goal_keywords=goal_keywords[:20],
            project_keywords=project_keywords[:10],
        )
    except Exception as e:
        logger.debug("load_profile_terms_failed", error=str(e))
        return ProfileTerms()


def _extract_item_terms(item: dict) -> set[str]:
    """Extract searchable terms from an intel item."""
    text_parts = []
    if item.get("title"):
        text_parts.append(item["title"])
    if item.get("summary"):
        text_parts.append(item["summary"])
    if item.get("content"):
        text_parts.append(item["content"][:500])

    text = " ".join(text_parts).lower()
    # Extract words (alphanumeric + hyphens for terms like "machine-learning")
    words = set(re.findall(r"[a-z][a-z0-9\-\.]*[a-z0-9]|[a-z]", text))

    # Also add tags
    tags = item.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    for tag in tags:
        if tag:
            words.add(tag.lower().strip())

    return words


def score_profile_relevance(item: dict, profile_terms: ProfileTerms) -> tuple[float, list[str]]:
    """Score an intel item's relevance to a user profile.

    Returns:
        Tuple of (score 0.0-1.0, list of matched aspect labels)
    """
    if profile_terms.is_empty:
        return 0.0, []

    item_terms = _extract_item_terms(item)
    if not item_terms:
        return 0.0, []

    matches = []
    weighted_score = 0.0

    # Skill match (weight: 0.25)
    skill_hits = profile_terms.skills & item_terms
    if skill_hits:
        skill_score = min(1.0, len(skill_hits) / max(1, min(3, len(profile_terms.skills))))
        weighted_score += 0.25 * skill_score
        matches.extend(f"skill:{h}" for h in sorted(skill_hits)[:3])

    # Tech match (weight: 0.25)
    tech_hits = profile_terms.tech & item_terms
    if tech_hits:
        tech_score = min(1.0, len(tech_hits) / max(1, min(3, len(profile_terms.tech))))
        weighted_score += 0.25 * tech_score
        matches.extend(f"tech:{h}" for h in sorted(tech_hits)[:3])

    # Interest/industry match (weight: 0.2)
    interest_hits = profile_terms.interests & item_terms
    if interest_hits:
        interest_score = min(1.0, len(interest_hits) / max(1, min(3, len(profile_terms.interests))))
        weighted_score += 0.2 * interest_score
        matches.extend(f"interest:{h}" for h in sorted(interest_hits)[:3])

    # Goal keyword match (weight: 0.2)
    goal_hits = profile_terms.goal_keywords & item_terms
    if goal_hits:
        goal_score = min(1.0, len(goal_hits) / max(1, min(3, len(profile_terms.goal_keywords))))
        weighted_score += 0.2 * goal_score
        matches.extend(f"goal:{h}" for h in sorted(goal_hits)[:2])

    # Project keyword match (weight: 0.1)
    project_hits = profile_terms.project_keywords & item_terms
    if project_hits:
        project_score = min(
            1.0, len(project_hits) / max(1, min(3, len(profile_terms.project_keywords)))
        )
        weighted_score += 0.1 * project_score
        matches.extend(f"project:{h}" for h in sorted(project_hits)[:2])

    return weighted_score, matches


class IntelSearch:
    """Combined semantic and keyword search for intel items."""

    def __init__(
        self,
        storage: IntelStorage,
        embedding_manager: Optional[IntelEmbeddingManager] = None,
    ):
        self.storage = storage
        self.embeddings = embedding_manager

    def semantic_search(
        self,
        query: str,
        n_results: int = 10,
        source_filter: Optional[str] = None,
    ) -> list[dict]:
        """Search using vector similarity.

        Falls back to keyword search if embeddings not available.
        """
        if not self.embeddings:
            return self.keyword_search(query, limit=n_results)

        where = {"source": source_filter} if source_filter else None
        results = self.embeddings.query(query, n_results=n_results, where=where)

        # Enrich results with full item data from storage
        enriched = []
        for result in results:
            try:
                item_id = int(result["id"])
                item = self._get_item_by_id(item_id)
                if item:
                    item["score"] = 1 - result["distance"]  # Convert distance to similarity
                    enriched.append(item)
            except (ValueError, TypeError):
                continue

        return enriched

    def keyword_search(
        self,
        query: str,
        limit: int = 20,
        source_filter: Optional[str] = None,
    ) -> list[dict]:
        """Keyword search — uses FTS5 when available, else LIKE fallback."""
        try:
            return self.storage.fts_search(query, limit=limit, source_filter=source_filter)
        except Exception:
            return self.storage.search(query, limit=limit, source_filter=source_filter)

    def hybrid_search(
        self,
        query: str,
        n_results: int = 10,
        semantic_weight: float = 0.7,
    ) -> list[dict]:
        """Combine semantic and keyword search results.

        Args:
            query: Search query
            n_results: Max results to return
            semantic_weight: Weight for semantic results (0-1)

        Returns:
            Merged and ranked results
        """
        semantic_results = self.semantic_search(query, n_results=n_results * 2)
        keyword_results = self.keyword_search(query, limit=n_results * 2)

        # Score fusion: combine results by URL
        scores = {}
        items = {}

        for i, item in enumerate(semantic_results):
            url = item.get("url", "")
            if url:
                rank_score = 1.0 / (i + 1)
                scores[url] = scores.get(url, 0) + rank_score * semantic_weight
                items[url] = item

        for i, item in enumerate(keyword_results):
            url = item.get("url", "")
            if url:
                rank_score = 1.0 / (i + 1)
                scores[url] = scores.get(url, 0) + rank_score * (1 - semantic_weight)
                if url not in items:
                    items[url] = item

        # Sort by combined score
        sorted_urls = sorted(scores.keys(), key=lambda u: scores[u], reverse=True)
        return [items[url] for url in sorted_urls[:n_results]]

    def profile_filtered_search(
        self,
        query: str,
        profile_terms: ProfileTerms,
        n_results: int = 5,
        min_relevance: float = 0.05,
        pool_multiplier: int = 4,
    ) -> list[dict]:
        """Search and re-rank results by profile relevance.

        Retrieves a broad candidate pool, scores each against the user's
        profile, filters below min_relevance, and returns re-ranked results
        annotated with match reasons.

        Args:
            query: Search query (ideally profile-augmented)
            profile_terms: Structured profile terms for scoring
            n_results: Desired number of final results
            min_relevance: Minimum relevance score to keep (0.0-1.0)
            pool_multiplier: How many times n_results to retrieve as candidates

        Returns:
            List of dicts with added 'profile_relevance' and 'match_reasons' fields
        """
        if profile_terms.is_empty:
            # No profile — fall back to standard search
            if self.embeddings:
                return self.hybrid_search(query, n_results=n_results)
            return self.keyword_search(query, limit=n_results)

        pool_size = n_results * pool_multiplier

        # Stage 1: Broad retrieval
        if self.embeddings:
            candidates = self.hybrid_search(query, n_results=pool_size)
        else:
            candidates = self.keyword_search(query, limit=pool_size)

        if not candidates:
            # Fallback to recent items, still filter them
            candidates = self.storage.get_recent(days=7, limit=pool_size)

        if not candidates:
            return []

        # Stage 2: Score against profile and filter
        scored = []
        for item in candidates:
            relevance, match_reasons = score_profile_relevance(item, profile_terms)
            if relevance >= min_relevance:
                item["profile_relevance"] = relevance
                item["match_reasons"] = match_reasons
                scored.append(item)

        # Sort by profile relevance (descending), break ties by original position
        scored.sort(key=lambda x: x["profile_relevance"], reverse=True)

        logger.debug(
            "profile_filtered_search",
            candidates=len(candidates),
            passed_filter=len(scored),
            min_relevance=min_relevance,
        )

        return scored[:n_results]

    def get_context_for_query(
        self,
        query: str,
        max_items: int = 5,
        max_chars: int = 3000,
    ) -> str:
        """Get intel context string for RAG.

        Args:
            query: User query
            max_items: Maximum items to include
            max_chars: Character limit for context

        Returns:
            Formatted context string
        """
        if self.embeddings:
            results = self.hybrid_search(query, n_results=max_items * 2)
        else:
            results = self.keyword_search(query, limit=max_items * 2)

        if not results:
            # Fallback to recent items
            results = self.storage.get_recent(days=7, limit=max_items)

        if not results:
            return "No external intelligence available."

        context_parts = []
        total_chars = 0

        for item in results[:max_items]:
            source = item.get("source", "unknown")
            title = item.get("title", "Untitled")
            summary = item.get("summary", "")[:200]
            url = item.get("url", "")

            entry = f"- [{source}] {title}"
            if summary:
                entry += f": {summary}"
            if url:
                entry += f" ({url})"

            if total_chars + len(entry) > max_chars:
                break

            context_parts.append(entry)
            total_chars += len(entry)

        return "\n".join(context_parts) if context_parts else "No relevant intelligence found."

    def get_filtered_context_for_query(
        self,
        query: str,
        profile_terms: ProfileTerms,
        max_items: int = 5,
        max_chars: int = 3000,
        min_relevance: float = 0.05,
    ) -> str:
        """Get intel context filtered and annotated by profile relevance.

        Like get_context_for_query but re-ranks by profile match and includes
        match annotations so the LLM can see why each item was selected.

        Falls back to standard get_context_for_query if profile is empty.
        """
        if profile_terms.is_empty:
            return self.get_context_for_query(query, max_items=max_items, max_chars=max_chars)

        results = self.profile_filtered_search(
            query,
            profile_terms,
            n_results=max_items,
            min_relevance=min_relevance,
        )

        if not results:
            # Fall back to unfiltered
            return self.get_context_for_query(query, max_items=max_items, max_chars=max_chars)

        context_parts = []
        total_chars = 0

        for item in results:
            source = item.get("source", "unknown")
            title = item.get("title", "Untitled")
            summary = item.get("summary", "")[:300]  # more context than before (was 200)
            url = item.get("url", "")
            match_reasons = item.get("match_reasons", [])
            relevance = item.get("profile_relevance", 0.0)

            entry = f"- [{source}] {title}"
            if summary:
                entry += f": {summary}"
            if url:
                entry += f" ({url})"
            if match_reasons:
                # Add annotation for LLM: which profile aspects this matches
                entry += f"\n  [Matches your: {', '.join(match_reasons[:5])}] (relevance: {relevance:.2f})"

            if total_chars + len(entry) > max_chars:
                break

            context_parts.append(entry)
            total_chars += len(entry)

        return "\n".join(context_parts) if context_parts else "No relevant intelligence found."

    def sync_embeddings(self) -> tuple[int, int]:
        """Sync all intel items to vector store.

        Returns:
            Tuple of (added, removed) counts
        """
        if not self.embeddings:
            return 0, 0

        # Get all items from storage
        with wal_connect(self.storage.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, source, title, url, summary, content, tags
                FROM intel_items
            """)
            rows = cursor.fetchall()

        # Prepare for embedding
        items = []
        for row in rows:
            content = f"{row['title']}\n{row['summary'] or ''}\n{row['content'] or ''}"
            items.append(
                {
                    "id": str(row["id"]),
                    "content": content,
                    "metadata": {
                        "source": row["source"],
                        "url": row["url"],
                        "tags": row["tags"] or "",
                    },
                }
            )

        return self.embeddings.sync_from_storage(items)

    def _get_item_by_id(self, item_id: int) -> Optional[dict]:
        """Fetch single item by ID."""
        try:
            with wal_connect(self.storage.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM intel_items WHERE id = ?",
                    (item_id,),
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except (sqlite3.OperationalError, Exception):
            return None
