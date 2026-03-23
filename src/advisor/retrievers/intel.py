"""Intel context retriever."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from db import wal_connect

if TYPE_CHECKING:
    from profile.storage import UserProfile

    from intelligence.search import IntelSearch

logger = structlog.get_logger()


class IntelRetriever:
    """Retrieves context from intelligence sources."""

    def __init__(
        self,
        intel_db_path: Path | None = None,
        intel_search: IntelSearch | None = None,
        profile_loader: Callable[[], UserProfile | None] | None = None,
        cache=None,
        user_id: str | None = None,
    ):
        self.intel_db_path = Path(intel_db_path).expanduser() if intel_db_path else None
        self.intel_search = intel_search
        self._profile_loader = profile_loader
        self.cache = cache
        self.user_id = user_id

    def get_intel_context(
        self,
        query: str,
        max_items: int = 5,
        max_chars: int = 3000,
    ) -> str:
        """Get relevant intelligence items for query."""
        if self.cache:
            key = self.cache.make_key("intel", query, max_items=max_items, max_chars=max_chars)
            cached = self.cache.get(key)
            if cached is not None:
                return cached

        result = self._get_intel_context_uncached(query, max_items=max_items, max_chars=max_chars)

        if self.cache:
            self.cache.set(key, result)
        return result

    def _get_intel_context_uncached(
        self,
        query: str,
        max_items: int = 5,
        max_chars: int = 3000,
    ) -> str:
        """Get intel context without cache layer."""
        if self.intel_search:
            return self.intel_search.get_context_for_query(
                query=query,
                max_items=max_items,
                max_chars=max_chars,
            )

        if not self.intel_db_path or not self.intel_db_path.exists():
            return "No external intelligence available yet."

        try:
            user_clause = ""
            user_params: tuple = ()
            if self.user_id:
                user_clause = "AND (user_id IS NULL OR user_id = ?)"
                user_params = (self.user_id,)

            with wal_connect(self.intel_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    f"""
                    SELECT title, source, summary, url, scraped_at
                    FROM intel_items
                    WHERE (title LIKE ? OR summary LIKE ?)
                    {user_clause}
                    ORDER BY scraped_at DESC
                    LIMIT ?
                """,
                    (f"%{query}%", f"%{query}%", *user_params, max_items * 2),
                )

                items = cursor.fetchall()

                if not items:
                    cursor = conn.execute(
                        f"""
                        SELECT title, source, summary, url, scraped_at
                        FROM intel_items
                        WHERE 1=1 {user_clause}
                        ORDER BY scraped_at DESC
                        LIMIT ?
                    """,
                        (*user_params, max_items),
                    )
                    items = cursor.fetchall()

            if not items:
                return "No external intelligence available."

            context_parts = []
            total_chars = 0

            for item in items[:max_items]:
                entry = f"- [{item['source']}] {item['title']}: {item['summary'][:200]}"
                if total_chars + len(entry) > max_chars:
                    break
                context_parts.append(entry)
                total_chars += len(entry)

            return "\n".join(context_parts) if context_parts else "No relevant intelligence found."

        except sqlite3.OperationalError:
            return "No external intelligence available."

    def get_filtered_intel_context(
        self,
        query: str,
        max_items: int = 5,
        max_chars: int = 3000,
        min_relevance: float = 0.05,
    ) -> str:
        """Get intel context filtered and annotated by profile relevance."""
        if not self.intel_search:
            return self.get_intel_context(query, max_items=max_items, max_chars=max_chars)

        profile_terms = self._load_profile_terms()

        return self.intel_search.get_filtered_context_for_query(
            query=query,
            profile_terms=profile_terms,
            max_items=max_items,
            max_chars=max_chars,
            min_relevance=min_relevance,
        )

    def _load_profile_terms(self):
        """Load profile and build ProfileTerms for intel filtering."""
        from intelligence.search import build_profile_terms

        profile = self._profile_loader() if self._profile_loader else None
        return build_profile_terms(profile)

    def get_ai_capabilities_context(self, query: str, max_chars: int = 1500) -> str:
        """Get AI capability context combining static KB + recent intel."""
        from advisor.ai_capabilities_kb import render_summary

        parts = []
        summary = render_summary()
        parts.append(summary)
        remaining = max_chars - len(summary) - 20

        if remaining > 100:
            ai_intel = self.get_intel_context(
                query + " AI capabilities benchmarks model performance",
                max_items=5,
                max_chars=remaining,
            )
            if ai_intel and "No" not in ai_intel[:10]:
                parts.append(ai_intel)

        return "\n\n".join(parts)

    def get_capability_context(self) -> str:
        """Load latest CapabilityHorizonModel and return horizon context."""
        try:
            from intelligence.capability_model import CapabilityHorizonModel

            db_path = self.intel_db_path
            if not db_path:
                return ""
            model = CapabilityHorizonModel(db_path)
            if model.load():
                return model.get_horizon_context()
        except Exception as e:
            logger.debug("capability_context_load_failed", error=str(e))
        return ""
