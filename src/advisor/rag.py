"""RAG retrieval combining journal and intelligence sources."""

from __future__ import annotations

import asyncio
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import structlog

from advisor.entity_retriever import EntityRetriever
from advisor.query_analyzer import QueryAnalysis, QueryAnalyzer, RetrievalMode
from advisor.query_decomposer import QueryDecomposer
from db import wal_connect
from intelligence.entity_store import EntityStore
from intelligence.search import IntelSearch
from journal.search import JournalSearch
from services.tokens import count_tokens

if TYPE_CHECKING:
    from services.reranker import CrossEncoderReranker

logger = structlog.get_logger()


@dataclass
class AskContext:
    """Consolidated context for ask() calls."""

    journal: str
    intel: str
    profile: str
    memory: str = ""
    thoughts: str = ""
    documents: str = ""
    entity_context: str = ""
    repo_context: str = ""


class RAGRetriever:
    """Retrieves relevant context for LLM queries."""

    def __init__(
        self,
        journal_search: JournalSearch,
        intel_db_path: Optional[Path] = None,
        intel_search: Optional[IntelSearch] = None,
        max_context_chars: int = 8000,
        max_context_tokens: int | None = None,
        journal_weight: float = 0.7,
        profile_path: Optional[str] = None,
        users_db_path: Optional[Path] = None,
        user_id: Optional[str] = None,
        cache=None,
        fact_store=None,
        memory_config: Optional[dict] = None,
        thread_store=None,
        library_index=None,
        entity_store: EntityStore | None = None,
        query_analyzer: QueryAnalyzer | None = None,
        query_decomposer: QueryDecomposer | None = None,
        entity_retriever: EntityRetriever | None = None,
        reranker: CrossEncoderReranker | None = None,
    ):
        self.journal = journal_search
        self.intel_db_path = Path(intel_db_path).expanduser() if intel_db_path else None
        self.intel_search = intel_search
        self.max_context_chars = max_context_chars
        self.max_context_tokens = (
            max_context_tokens if max_context_tokens is not None else max_context_chars // 4
        )
        self.journal_weight = journal_weight
        self._profile_path = profile_path or "~/coach/profile.yaml"
        self._users_db_path = users_db_path
        self._user_id = user_id
        self.cache = cache
        self._fact_store = fact_store
        self._memory_config = memory_config or {}
        self._thread_store = thread_store
        self._library_index = library_index
        self.entity_store = entity_store
        self.query_analyzer = query_analyzer
        self.query_decomposer = query_decomposer
        self.entity_retriever = entity_retriever
        self.reranker = reranker

    def get_profile_context(self, structured: bool = False) -> str:
        """Load user profile summary for LLM context injection.

        Args:
            structured: If True, return multi-section structured format
                        optimized for recommendation prompts. If False,
                        return compact one-line summary.
        """
        try:
            from profile.storage import ProfileStorage

            ps = ProfileStorage(self._profile_path)
            profile = ps.load()
            if profile:
                if structured:
                    return f"\n{profile.structured_summary()}\n"
                return f"\nUSER PROFILE: {profile.summary()}\n"
        except Exception as e:
            logger.debug("profile_load_skipped", error=str(e))
        return ""

    def get_repo_context(self, query: str) -> str:
        """Inject GitHub repo health data when query matches a monitored repo."""
        if not self._user_id or not self.intel_db_path:
            return ""
        try:
            from intelligence.github_repo_store import GitHubRepoStore

            store = GitHubRepoStore(self.intel_db_path)
            repos = store.list_repos(self._user_id)
            if not repos:
                return ""

            query_tokens = set(query.lower().split())
            max_chars = int(self.max_context_chars * 0.05)
            blocks = []
            chars_used = 0

            for repo in repos:
                # Check if query references this repo or its linked goal
                repo_name = repo.repo_full_name.split("/")[-1].lower()
                goal_tokens = set()
                if repo.linked_goal_path:
                    goal_title = (
                        repo.linked_goal_path.rsplit("/", 1)[-1]
                        .replace(".md", "")
                        .replace("-", " ")
                    )
                    goal_tokens = set(goal_title.lower().split())

                match_tokens = {repo_name} | goal_tokens
                if not (query_tokens & match_tokens):
                    continue

                snapshot = store.get_latest_snapshot(repo.id)
                if not snapshot:
                    continue

                # Compute trend from weekly commits
                trend = "unknown"
                wc = snapshot.weekly_commits
                if len(wc) >= 8:
                    recent = sum(wc[-4:]) / 4.0
                    prior = sum(wc[-8:-4]) / 4.0
                    if recent > prior * 1.2:
                        trend = "increasing"
                    elif recent < prior * 0.8:
                        trend = "declining"
                    else:
                        trend = "steady"

                goal_attr = ""
                if repo.linked_goal_path:
                    goal_title = (
                        repo.linked_goal_path.rsplit("/", 1)[-1]
                        .replace(".md", "")
                        .replace("-", " ")
                    )
                    goal_attr = f' linked_goal="{goal_title}"'

                pushed = (
                    snapshot.pushed_at.strftime("%Y-%m-%d") if snapshot.pushed_at else "unknown"
                )
                block = (
                    f'<github_project repo="{repo.repo_full_name}"{goal_attr}>\n'
                    f"  Last commit: {pushed}\n"
                    f"  Commits (30d): {snapshot.commits_30d} ({trend})\n"
                    f"  Open issues: {snapshot.open_issues} | Open PRs: {snapshot.open_prs}\n"
                    f"  CI: {snapshot.ci_status}\n"
                    f"  Latest release: {snapshot.latest_release or 'none'}\n"
                    f"</github_project>"
                )
                if chars_used + len(block) > max_chars:
                    break
                blocks.append(block)
                chars_used += len(block)

            return "\n".join(blocks)
        except Exception as e:
            logger.debug("repo_context_skipped", error=str(e))
            return ""

    def build_context_for_ask(
        self,
        query: str,
        rag_config: dict | None = None,
        attachment_ids: list[str] | None = None,
    ) -> "AskContext":
        """Build consolidated context for ask() calls.

        Args:
            query: User question
            rag_config: Dict of RAG flags (structured_profile, inject_memory,
                        inject_recurring_thoughts, inject_documents, xml_delimiters)

        Returns:
            AskContext with all context slots populated per flags
        """
        cfg = rag_config or {}

        enhanced = self.get_enhanced_context(query)
        profile_ctx = self.get_profile_context(structured=cfg.get("structured_profile", False))

        memory_ctx = ""
        if cfg.get("inject_memory", False):
            memory_ctx = self.get_memory_context(query)

        thoughts_ctx = ""
        if cfg.get("inject_recurring_thoughts", False):
            thoughts_ctx = self.get_recurring_thoughts_context()

        documents_ctx = ""
        if cfg.get("inject_documents", False) or attachment_ids:
            documents_ctx = self.get_document_context(query, attachment_ids=attachment_ids)

        repo_ctx = ""
        if cfg.get("inject_repo_context", True):
            repo_ctx = self.get_repo_context(query)

        return AskContext(
            journal=enhanced.journal,
            intel=enhanced.intel,
            profile=profile_ctx,
            memory=memory_ctx,
            thoughts=thoughts_ctx,
            documents=documents_ctx,
            entity_context=enhanced.entity_context,
            repo_context=repo_ctx,
        )

    def get_document_context(
        self,
        query: str,
        attachment_ids: list[str] | None = None,
        max_items: int = 4,
        max_chars: int = 4000,
    ) -> str:
        """Get indexed Library document context for the current ask."""
        if not self._library_index:
            return ""

        selected: list[dict] = []
        seen_ids: set[str] = set()
        remaining_chars = max_chars

        def add_item(item: dict | None) -> None:
            nonlocal remaining_chars
            if not item:
                return
            report_id = item.get("report_id")
            if not report_id or report_id in seen_ids or len(selected) >= max_items:
                return

            text = (item.get("extracted_text") or item.get("body_text") or "").strip()
            if not text:
                return

            excerpt = text[: min(len(text), max(remaining_chars - 200, 0))].strip()
            if not excerpt:
                return

            selected.append(
                {
                    "report_id": report_id,
                    "title": item.get("title") or "Untitled document",
                    "file_name": item.get("file_name") or "",
                    "source_kind": item.get("source_kind") or "document",
                    "excerpt": excerpt,
                }
            )
            seen_ids.add(report_id)
            remaining_chars -= len(excerpt)

        for attachment_id in attachment_ids or []:
            add_item(self._library_index.get_item_text(attachment_id))
            if remaining_chars <= 0 or len(selected) >= max_items:
                break

        if query and remaining_chars > 0 and len(selected) < max_items:
            for hit in self._library_index.hybrid_search(
                query, limit=max_items * 2, status="ready"
            ):
                add_item(self._library_index.get_item_text(hit["id"]))
                if remaining_chars <= 0 or len(selected) >= max_items:
                    break

        if not selected:
            return ""

        blocks = []
        for item in selected:
            file_label = f" ({item['file_name']})" if item["file_name"] else ""
            blocks.append(f"[DOCUMENT] {item['title']}{file_label}\n{item['excerpt']}")
        return "DOCUMENT CONTEXT:\n" + "\n\n".join(blocks)

    def get_profile_keywords(self) -> list[str]:
        """Extract key terms from profile for intel query augmentation."""
        try:
            from profile.storage import ProfileStorage

            ps = ProfileStorage(self._profile_path)
            profile = ps.load()
            if not profile:
                return []

            keywords = []
            if profile.skills:
                keywords.extend(s.name for s in profile.skills[:8])
            keywords.extend(profile.languages_frameworks[:6])
            keywords.extend(profile.technologies_watching[:6])
            keywords.extend(profile.industries_watching[:4])
            keywords.extend(profile.interests[:4])
            # Extract key terms from active projects
            for p in profile.active_projects[:3]:
                keywords.extend(p.lower().split()[:3])
            return [k.lower().strip() for k in keywords if k.strip()]
        except Exception:
            return []

    def get_memory_context(self, query: str = "") -> str:
        """Get distilled memory block for system prompt injection.

        Returns formatted fact block grouped by category, or empty string
        if memory is disabled or no facts exist.
        """
        if not self._fact_store:
            return ""

        try:
            max_facts = self._memory_config.get("max_context_facts", 25)
            high_conf = self._memory_config.get("high_confidence_threshold", 0.9)
            thread_boosts = self._get_thread_fact_boosts()

            # Semantic search for query-relevant facts
            relevant = []
            if query:
                relevant = self._fact_store.search(query, limit=max_facts)

            # Always include high-confidence facts
            all_active = self._fact_store.get_all_active()
            high_conf_facts = [
                f
                for f in all_active
                if self._effective_fact_confidence(f, thread_boosts) >= high_conf
            ]

            # Merge, dedup by ID, cap at max
            seen = set()
            merged = []
            ranked_candidates = sorted(
                high_conf_facts + relevant,
                key=lambda fact: self._effective_fact_confidence(fact, thread_boosts),
                reverse=True,
            )
            for f in ranked_candidates:
                if f.id not in seen:
                    seen.add(f.id)
                    merged.append(f)
                if len(merged) >= max_facts:
                    break

            if not merged:
                return ""

            # Fetch observations separately
            observations = []
            try:
                observations = self._fact_store.get_all_active_observations()
            except Exception:
                pass

            return self._format_memory_block(
                merged, thread_boosts=thread_boosts, observations=observations
            )
        except Exception as e:
            logger.debug("memory_context_failed", error=str(e))
            return ""

    def _format_memory_block(
        self,
        facts: list,
        thread_boosts: dict[str, float] | None = None,
        observations: list | None = None,
    ) -> str:
        """Format facts into grouped system prompt block."""
        from memory.models import FactCategory

        category_labels = {
            FactCategory.PREFERENCE: "Preferences",
            FactCategory.SKILL: "Skills",
            FactCategory.CONSTRAINT: "Constraints",
            FactCategory.PATTERN: "Patterns",
            FactCategory.CONTEXT: "Current Context",
            FactCategory.GOAL_CONTEXT: "Goal Context",
        }

        lines = ["<user_memory>"]

        # Observations section first
        if observations:
            lines.append("## Observations")
            for obs in sorted(observations, key=lambda x: x.confidence, reverse=True):
                lines.append(f"* {obs.text}")
            lines.append("")

        # Group raw facts by category (exclude observations from raw listing)
        grouped: dict[str, list] = {}
        for f in facts:
            if f.category == FactCategory.OBSERVATION:
                continue
            label = category_labels.get(f.category, str(f.category))
            grouped.setdefault(label, []).append(f)

        display_order = [
            "Current Context",
            "Goal Context",
            "Preferences",
            "Skills",
            "Constraints",
            "Patterns",
        ]
        for section in display_order:
            if section not in grouped:
                continue
            lines.append(f"## {section}")
            for f in sorted(
                grouped[section],
                key=lambda x: self._effective_fact_confidence(x, thread_boosts or {}),
                reverse=True,
            ):
                lines.append(f"- {f.text}")
            lines.append("")

        lines.append("</user_memory>")
        return "\n".join(lines)

    def get_recurring_thoughts_context(self, max_threads: int = 3) -> str:
        """Get active recurring thought threads for system prompt injection.

        Returns <recurring_thoughts> XML block, or empty string if no threads.
        """
        if not self._thread_store:
            return ""

        try:
            from datetime import datetime, timedelta

            threads = self._run_async(self._thread_store.get_active_threads(min_entries=2))

            if not threads:
                return ""

            now = datetime.now()
            thirty_days_ago = now - timedelta(days=30)

            # Compute entries_last_30_days for sorting
            scored = []
            for t in threads:
                entries = self._run_async(self._thread_store.get_thread_entries(t.id))
                recent_count = sum(1 for e in entries if e.entry_date >= thirty_days_ago)
                first_date = min(e.entry_date for e in entries) if entries else t.created_at
                last_date = max(e.entry_date for e in entries) if entries else t.updated_at
                weeks_span = max(1, (last_date - first_date).days // 7)
                days_since_last = (now - last_date).days

                scored.append(
                    {
                        "thread": t,
                        "strength": getattr(t, "strength", 0.0),
                        "recent_count": recent_count,
                        "weeks_span": weeks_span,
                        "days_since_last": days_since_last,
                    }
                )

            scored.sort(
                key=lambda x: (x["strength"], x["recent_count"], -x["days_since_last"]),
                reverse=True,
            )
            top = scored[:max_threads]

            if not any(s["strength"] > 0.05 for s in top):
                return ""

            lines = ["<recurring_thoughts>", "The user has persistent recurring thoughts:"]
            for i, s in enumerate(top, 1):
                t = s["thread"]
                ago = s["days_since_last"]
                ago_str = "today" if ago == 0 else f"{ago} days ago"
                lines.append(
                    f'{i}. "{t.label}" — {t.entry_count} entries over '
                    f"{s['weeks_span']} weeks, last {ago_str}"
                )
            lines.append("</recurring_thoughts>")
            return "\n".join(lines)
        except Exception as e:
            logger.debug("recurring_thoughts_failed", error=str(e))
            return ""

    def _get_thread_fact_boosts(self) -> dict[str, float]:
        """Map source entry IDs to a small confidence bonus from strong threads."""
        if not self._thread_store:
            return {}

        boosts: dict[str, float] = {}
        try:
            threads = self._run_async(self._thread_store.get_active_threads(min_entries=2))
            for thread in threads:
                strength = float(getattr(thread, "strength", 0.0))
                if strength <= 0.5:
                    continue
                bonus = min(0.1, max(0.0, (strength - 0.5) * 0.2))
                if bonus <= 0:
                    continue
                entries = self._run_async(self._thread_store.get_thread_entries(thread.id))
                for entry in entries:
                    boosts[entry.entry_id] = max(boosts.get(entry.entry_id, 0.0), bonus)
        except Exception as exc:
            logger.debug("thread_fact_boosts_failed", error=str(exc))
        return boosts

    @staticmethod
    def _effective_fact_confidence(fact, thread_boosts: dict[str, float]) -> float:
        return min(1.0, fact.confidence + thread_boosts.get(fact.source_id, 0.0))

    def get_journal_context(
        self,
        query: str,
        max_entries: int = 5,
        max_chars: int = 6000,
        entry_type: Optional[str] = None,
    ) -> str:
        """Get relevant journal entries for query."""
        if self.cache:
            key = self.cache.make_key(
                "journal", query, max_entries=max_entries, max_chars=max_chars
            )
            cached = self.cache.get(key)
            if cached is not None:
                return cached

        result = self.journal.get_context_for_query(
            query=query,
            max_entries=max_entries,
            max_chars=max_chars,
        )

        if self.cache:
            self.cache.set(key, result)
        return result

    def _load_profile_terms(self):
        """Load profile and build ProfileTerms for intel filtering."""
        from intelligence.search import load_profile_terms

        return load_profile_terms(self._profile_path)

    def get_filtered_intel_context(
        self,
        query: str,
        max_items: int = 5,
        max_chars: int = 3000,
        min_relevance: float = 0.05,
    ) -> str:
        """Get intel context filtered and annotated by profile relevance.

        Two-stage pipeline:
        1. Broad retrieval using profile-augmented query
        2. Re-rank by profile term overlap, filter below threshold, annotate matches

        Falls back to standard get_intel_context if IntelSearch not available
        or profile is empty.
        """
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

    def get_intel_context(
        self,
        query: str,
        max_items: int = 5,
        max_chars: int = 3000,
    ) -> str:
        """Get relevant intelligence items for query.

        Uses semantic search if IntelSearch is configured, falls back to keyword search.
        """
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
        # Use semantic search if available
        if self.intel_search:
            return self.intel_search.get_context_for_query(
                query=query,
                max_items=max_items,
                max_chars=max_chars,
            )

        # Fallback to basic keyword search
        if not self.intel_db_path or not self.intel_db_path.exists():
            return "No external intelligence available yet."

        try:
            with wal_connect(self.intel_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT title, source, summary, url, scraped_at
                    FROM intel_items
                    WHERE title LIKE ? OR summary LIKE ?
                    ORDER BY scraped_at DESC
                    LIMIT ?
                """,
                    (f"%{query}%", f"%{query}%", max_items * 2),
                )

                items = cursor.fetchall()

                if not items:
                    cursor = conn.execute(
                        """
                        SELECT title, source, summary, url, scraped_at
                        FROM intel_items
                        ORDER BY scraped_at DESC
                        LIMIT ?
                    """,
                        (max_items,),
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

    def compute_dynamic_weight(self, user_id: Optional[str] = None, query: str = "") -> float:
        """Compute journal_weight from engagement data.

        Base formula uses journal vs intel engagement, then applies a small
        query-aligned tilt from recommendation engagement categories.
        """
        uid = user_id or self._user_id
        if not uid or not self._users_db_path:
            return self.journal_weight

        try:
            with wal_connect(self._users_db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT target_type, event_type, COUNT(*) as cnt
                    FROM engagement_events
                    WHERE user_id = ? AND created_at >= datetime('now', '-30 days')
                    GROUP BY target_type, event_type
                    """,
                    (uid,),
                ).fetchall()

            total = sum(r["cnt"] for r in rows)
            if total < 10:
                return self.journal_weight

            positive_events = {"opened", "saved", "acted_on", "feedback_useful"}
            journal_score = sum(
                r["cnt"]
                for r in rows
                if r["target_type"] == "journal" and r["event_type"] in positive_events
            )
            intel_score = sum(
                r["cnt"]
                for r in rows
                if r["target_type"] == "intel" and r["event_type"] in positive_events
            )
            denom = journal_score + intel_score
            if denom == 0:
                return self.journal_weight

            journal_ratio = journal_score / denom
            weight = 0.7 + 0.15 * (journal_ratio - 0.5)
            weight += self._recommendation_weight_adjustment(uid, query)
            return max(0.5, min(0.85, weight))
        except Exception as e:
            logger.debug("dynamic_weight_fallback", error=str(e))
            return self.journal_weight

    def _recommendation_weight_adjustment(self, user_id: str, query: str) -> float:
        """Tilt journal vs intel weight when the query aligns with engaged categories."""
        if not query.strip():
            return 0.0

        try:
            from advisor.recommendations import CATEGORY_QUERIES
        except Exception:
            return 0.0

        query_terms = {token for token in query.lower().split() if token}
        if not query_terms:
            return 0.0

        category_direction = {
            "learning": 0.05,
            "career": 0.04,
            "entrepreneurial": 0.03,
            "projects": 0.03,
            "investment": -0.05,
        }

        try:
            with wal_connect(self._users_db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT json_extract(metadata_json, '$.category') as category,
                           event_type,
                           COUNT(*) as cnt
                    FROM engagement_events
                    WHERE user_id = ?
                      AND target_type = 'recommendation'
                      AND event_type IN ('feedback_useful', 'feedback_irrelevant')
                      AND created_at >= datetime('now', '-30 days')
                    GROUP BY category, event_type
                    """,
                    (user_id,),
                ).fetchall()
        except Exception as exc:
            logger.debug("recommendation_weight_adjustment_failed", error=str(exc))
            return 0.0

        counts: dict[str, dict[str, int]] = {}
        for row in rows:
            category = row["category"] or "unknown"
            counts.setdefault(category, {"feedback_useful": 0, "feedback_irrelevant": 0})
            counts[category][row["event_type"]] += row["cnt"]

        adjustment = 0.0
        for category, query_text in CATEGORY_QUERIES.items():
            if category not in counts or category not in category_direction:
                continue
            category_terms = {token for token in query_text.lower().split() if token}
            if not (query_terms & category_terms):
                continue
            useful = counts[category]["feedback_useful"]
            irrelevant = counts[category]["feedback_irrelevant"]
            total = useful + irrelevant
            if total < 4:
                continue
            sentiment = (useful - irrelevant) / total
            adjustment += category_direction[category] * sentiment

        return max(-0.05, min(0.05, adjustment))

    def _resolve_journal_weight(
        self,
        query: str = "",
        journal_weight: Optional[float] = None,
    ) -> float:
        if journal_weight is not None:
            return journal_weight
        if self._users_db_path and self._user_id:
            return self.compute_dynamic_weight(query=query)
        return self.journal_weight

    def _tokens_to_chars(self, tokens: int) -> int:
        """Convert a token budget to an approximate char budget (4 chars/token)."""
        return tokens * 4

    def _get_text_context_for_budget(
        self,
        query: str,
        total_chars: int,
        journal_weight: Optional[float] = None,
    ) -> tuple[str, str]:
        weight = self._resolve_journal_weight(query, journal_weight)
        journal_chars = int(total_chars * weight)
        intel_chars = total_chars - journal_chars
        journal_ctx = self.get_journal_context(query, max_chars=journal_chars)
        intel_ctx = self.get_intel_context(query, max_chars=intel_chars)
        return self._truncate_to_token_budget(journal_ctx, intel_ctx, weight)

    def _get_temporal_context(
        self,
        query: str,
        analysis: QueryAnalysis,
        total_chars: int,
    ) -> tuple[str, str]:
        """Retrieve context using temporal filtering on both journal and intel."""
        tf = analysis.temporal_filter
        search_query = analysis.cleaned_query or query
        weight = self._resolve_journal_weight(search_query)
        journal_chars = int(total_chars * weight)
        intel_chars = total_chars - journal_chars

        # Journal temporal search
        journal_results = self.journal.temporal_search(
            search_query, start=tf.start, end=tf.end, n_results=5
        )
        if journal_results:
            # Format journal results the same way get_context_for_query does
            parts = []
            total = 0
            for r in journal_results:
                entry_text = (
                    f"\n--- Entry: {r['title']} ({r['type']}) ---\n"
                    f"Date: {r['created']}\n"
                    f"Tags: {', '.join(r['tags']) if r['tags'] else 'none'}\n\n"
                    f"{r['content']}\n"
                )
                if total + len(entry_text) > journal_chars:
                    remaining = journal_chars - total
                    if remaining > 200:
                        parts.append(entry_text[:remaining] + "...[truncated]")
                    break
                parts.append(entry_text)
                total += len(entry_text)
            journal_ctx = "\n".join(parts) if parts else "No relevant journal entries found."
        else:
            journal_ctx = "No relevant journal entries found."

        # Intel temporal search
        if self.intel_search:
            intel_results = self.intel_search.temporal_search(
                search_query, start=tf.start, end=tf.end, n_results=5
            )
            if intel_results:
                parts = []
                total = 0
                for item in intel_results:
                    source = item.get("source", "unknown")
                    title = item.get("title", "Untitled")
                    summary = item.get("summary", "")[:200]
                    url = item.get("url", "")
                    entry = f"- [{source}] {title}"
                    if summary:
                        entry += f": {summary}"
                    if url:
                        entry += f" ({url})"
                    if total + len(entry) > intel_chars:
                        break
                    parts.append(entry)
                    total += len(entry)
                intel_ctx = "\n".join(parts) if parts else "No relevant intelligence found."
            else:
                intel_ctx = "No relevant intelligence found."
        else:
            intel_ctx = self.get_intel_context(search_query, max_chars=intel_chars)

        return self._truncate_to_token_budget(journal_ctx, intel_ctx, weight)

    def _truncate_to_token_budget(
        self, journal_ctx: str, intel_ctx: str, weight: float
    ) -> tuple[str, str]:
        """Ensure combined context fits within max_context_tokens."""
        total_tokens = count_tokens(journal_ctx) + count_tokens(intel_ctx)
        if total_tokens <= self.max_context_tokens:
            return journal_ctx, intel_ctx

        # Proportionally truncate the larger context
        journal_budget = int(self.max_context_tokens * weight)
        intel_budget = self.max_context_tokens - journal_budget

        journal_tokens = count_tokens(journal_ctx)
        if journal_tokens > journal_budget:
            # Rough truncation: cut chars proportionally
            ratio = journal_budget / max(journal_tokens, 1)
            journal_ctx = journal_ctx[: int(len(journal_ctx) * ratio)]

        intel_tokens = count_tokens(intel_ctx)
        if intel_tokens > intel_budget:
            ratio = intel_budget / max(intel_tokens, 1)
            intel_ctx = intel_ctx[: int(len(intel_ctx) * ratio)]

        return journal_ctx, intel_ctx

    def get_combined_context(
        self,
        query: str,
        journal_weight: Optional[float] = None,
    ) -> tuple[str, str]:
        """Get both journal and intel context.

        Args:
            query: User query
            journal_weight: Proportion of context budget for journal (0-1)

        Returns:
            Tuple of (journal_context, intel_context)
        """
        weight = self._resolve_journal_weight(query, journal_weight)
        total_chars = self.max_context_chars

        if self.cache:
            key = self.cache.make_key("combined", query, weight=weight, total_chars=total_chars)
            cached = self.cache.get(key)
            if cached is not None:
                import json

                parts = json.loads(cached)
                return parts["journal"], parts["intel"]

        journal_ctx, intel_ctx = self._get_text_context_for_budget(query, total_chars, weight)

        if self.cache:
            import json

            self.cache.set(key, json.dumps({"journal": journal_ctx, "intel": intel_ctx}))

        return journal_ctx, intel_ctx

    def get_enhanced_context(self, query: str) -> AskContext:
        """Get text and optional entity context for advisor prompts."""
        if not self.query_analyzer:
            journal_ctx, intel_ctx = self.get_combined_context(query)
            return AskContext(journal=journal_ctx, intel=intel_ctx, profile="")

        try:
            analysis: QueryAnalysis = self.query_analyzer.analyze(query)
        except Exception as exc:
            logger.warning("enhanced_context_analysis_failed", error=str(exc))
            journal_ctx, intel_ctx = self.get_combined_context(query)
            return AskContext(journal=journal_ctx, intel=intel_ctx, profile="")

        entity_budget = 0
        entity_context = ""
        if (
            analysis.mode in {RetrievalMode.ENTITY, RetrievalMode.COMBINED}
            and self.entity_retriever
        ):
            entity_budget = int(self.max_context_chars * 0.2)
            try:
                entity_context = self.entity_retriever.retrieve(analysis.matched_entities, query)
            except Exception as exc:
                logger.warning("entity_context_failed", error=str(exc))
                entity_context = ""
        if entity_context:
            entity_context = entity_context[:entity_budget]
            text_budget = self.max_context_chars - len(entity_context)
        else:
            text_budget = self.max_context_chars

        # Temporal routing — orthogonal to mode dispatch
        if analysis.temporal_filter:
            journal_ctx, intel_ctx = self._get_temporal_context(query, analysis, text_budget)
        elif (
            analysis.mode in {RetrievalMode.DECOMPOSED, RetrievalMode.COMBINED}
            and self.query_decomposer
        ):
            journal_ctx, intel_ctx = self._run_async(
                self._decomposed_retrieval(query, total_chars=text_budget)
            )
        else:
            journal_ctx, intel_ctx = self._get_text_context_for_budget(query, text_budget)

        # Optional cross-encoder reranking on final context
        if self.reranker and getattr(self.reranker, "available", False):
            journal_ctx, intel_ctx = self._apply_reranker(query, journal_ctx, intel_ctx)

        return AskContext(
            journal=journal_ctx,
            intel=intel_ctx,
            profile="",
            entity_context=entity_context,
        )

    def _apply_reranker(self, query: str, journal_ctx: str, intel_ctx: str) -> tuple[str, str]:
        """Rerank context passages using cross-encoder."""
        try:
            # Rerank intel passages (each line is a passage)
            intel_lines = [line for line in intel_ctx.split("\n") if line.strip()]
            if len(intel_lines) > 1:
                indices = self.reranker.rerank(query, intel_lines, top_k=len(intel_lines))
                intel_ctx = "\n".join(intel_lines[i] for i in indices)
        except Exception as exc:
            logger.debug("reranker_apply_failed", error=str(exc))
        return journal_ctx, intel_ctx

    async def _decomposed_retrieval(
        self,
        query: str,
        total_chars: int,
    ) -> tuple[str, str]:
        sub_questions = await self.query_decomposer.decompose(query)
        if len(sub_questions) == 1:
            return self._get_text_context_for_budget(sub_questions[0], total_chars)

        results = await asyncio.gather(
            *[
                asyncio.to_thread(self._get_text_context_for_budget, sub_query, total_chars)
                for sub_query in sub_questions
            ],
            return_exceptions=True,
        )
        journal_parts = []
        intel_parts = []
        for result in results:
            if isinstance(result, Exception):
                continue
            journal_parts.append(result[0])
            intel_parts.append(result[1])
        if not journal_parts and not intel_parts:
            return self._get_text_context_for_budget(query, total_chars)

        weight = self._resolve_journal_weight(query)
        journal_budget = int(total_chars * weight)
        intel_budget = total_chars - journal_budget
        return (
            self._merge_context_lines(journal_parts, journal_budget),
            self._merge_context_lines(intel_parts, intel_budget),
        )

    def _merge_context_lines(self, contexts: list[str], max_chars: int) -> str:
        scores: dict[str, int] = {}
        lines_by_key: dict[str, str] = {}
        order: list[str] = []
        for context in contexts:
            for raw_line in context.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                key = self._line_key(line)
                if key not in lines_by_key:
                    lines_by_key[key] = line
                    order.append(key)
                scores[key] = scores.get(key, 0) + 1
        merged = []
        total = 0
        for key in sorted(order, key=lambda value: (-scores[value], order.index(value))):
            line = lines_by_key[key]
            if total + len(line) + 1 > max_chars:
                break
            merged.append(line)
            total += len(line) + 1
        return "\n".join(merged)

    @staticmethod
    def _line_key(line: str) -> str:
        import re

        match = re.search(r"\((https?://[^)]+)\)", line)
        return match.group(1) if match else line.lower()

    @staticmethod
    def _run_async(coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        import threading

        result = {}
        error = {}

        def runner():
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                result["value"] = loop.run_until_complete(coro)
            except Exception as exc:
                error["value"] = exc
            finally:
                loop.close()

        thread = threading.Thread(target=runner)
        thread.start()
        thread.join()
        if "value" in error:
            raise error["value"]
        return result["value"]

    def get_capability_context(self) -> str:
        """Load latest CapabilityHorizonModel and return horizon context.

        Intended for injection into entrepreneurial, career, investment,
        and learning recommendation categories only.
        """
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

    def get_ai_capabilities_context(self, query: str, max_chars: int = 1500) -> str:
        """Get AI capability context combining static KB + recent intel.

        Args:
            query: User query to match against AI capability intel
            max_chars: Max total characters for combined context

        Returns:
            Combined context string with KB summary + relevant scraped items
        """
        from advisor.ai_capabilities_kb import render_summary

        parts = []
        # Static KB summary (~500 chars)
        summary = render_summary()
        parts.append(summary)
        remaining = max_chars - len(summary) - 20

        # Recent AI capabilities intel from scraper
        if remaining > 100:
            ai_intel = self.get_intel_context(
                query + " AI capabilities benchmarks model performance",
                max_items=5,
                max_chars=remaining,
            )
            if ai_intel and "No" not in ai_intel[:10]:
                parts.append(ai_intel)

        return "\n\n".join(parts)

    def get_recent_entries(self, days: int = 7, max_chars: int = 6000) -> str:
        """Get recent journal entries for weekly review."""
        # For weekly review, use recency-based retrieval
        entries = self.journal.storage.list_entries(limit=20)

        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(days=days)

        recent = []
        total_chars = 0

        for entry in entries:
            try:
                created = entry.get("created")
                if created:
                    entry_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if entry_date.replace(tzinfo=None) < cutoff:
                        continue

                post = self.journal.storage.read(entry["path"])
                entry_text = f"""
--- {entry["title"]} ({entry["type"]}) ---
{post.content}
"""
                if total_chars + len(entry_text) > max_chars:
                    break

                recent.append(entry_text)
                total_chars += len(entry_text)

            except (OSError, ValueError) as e:
                logger.warning(
                    "journal_entry_read_failed", path=str(entry.get("path")), error=str(e)
                )
                continue

        if not recent:
            return "No journal entries from the past week."

        return "\n".join(recent)

    def get_research_context(
        self,
        query: str,
        max_entries: int = 3,
        max_chars: int = 4000,
    ) -> str:
        """Get relevant research reports for query.

        Args:
            query: User query to match against research
            max_entries: Max research entries to include
            max_chars: Max total characters

        Returns:
            Formatted research context string
        """
        # Search research entries via journal
        research_entries = self.journal.storage.list_entries(
            entry_type="research",
            limit=max_entries * 2,
        )

        if not research_entries:
            return ""

        # Use semantic search if available to rank by relevance
        if hasattr(self.journal, "semantic_search"):
            results = self.journal.semantic_search(
                query,
                n_results=max_entries,
                entry_type="research",
            )
            if results:
                context_parts = []
                total_chars = 0
                for r in results:
                    label = r.get("title", "Unknown")
                    if r.get("change_summary"):
                        label = f"{label} — {r.get('change_summary')}"
                    text = f"[Research: {label}]\n{r.get('content', '')[:1500]}\n"
                    if total_chars + len(text) > max_chars:
                        break
                    context_parts.append(text)
                    total_chars += len(text)
                return "\n".join(context_parts) if context_parts else ""

        # Fallback: return most recent research
        context_parts = []
        total_chars = 0

        for entry in research_entries[:max_entries]:
            try:
                post = self.journal.storage.read(entry["path"])
                label = entry["title"]
                if post.get("change_summary"):
                    label = f"{label} — {post.get('change_summary')}"
                text = f"[Research: {label}]\n{post.content[:1500]}\n"
                if total_chars + len(text) > max_chars:
                    break
                context_parts.append(text)
                total_chars += len(text)
            except (OSError, ValueError) as e:
                logger.warning(
                    "research_entry_read_failed", path=str(entry.get("path")), error=str(e)
                )
                continue

        return "\n".join(context_parts) if context_parts else ""

    def get_full_context(
        self,
        query: str,
        include_research: bool = True,
    ) -> tuple[str, str, str]:
        """Get journal, intel, and research context.

        Returns:
            Tuple of (journal_context, intel_context, research_context)
        """
        journal_ctx, intel_ctx = self.get_combined_context(query)
        research_ctx = self.get_research_context(query) if include_research else ""
        return journal_ctx, intel_ctx, research_ctx
