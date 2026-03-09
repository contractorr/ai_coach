"""RAG retrieval combining journal and intelligence sources."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

from db import wal_connect
from intelligence.search import IntelSearch
from journal.search import JournalSearch

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


class RAGRetriever:
    """Retrieves relevant context for LLM queries."""

    def __init__(
        self,
        journal_search: JournalSearch,
        intel_db_path: Optional[Path] = None,
        intel_search: Optional[IntelSearch] = None,
        max_context_chars: int = 8000,
        journal_weight: float = 0.7,
        profile_path: Optional[str] = None,
        users_db_path: Optional[Path] = None,
        user_id: Optional[str] = None,
        cache=None,
        fact_store=None,
        memory_config: Optional[dict] = None,
        thread_store=None,
        library_index=None,
    ):
        self.journal = journal_search
        self.intel_db_path = Path(intel_db_path).expanduser() if intel_db_path else None
        self.intel_search = intel_search
        self.max_context_chars = max_context_chars
        self.journal_weight = journal_weight
        self._profile_path = profile_path or "~/coach/profile.yaml"
        self._users_db_path = users_db_path
        self._user_id = user_id
        self.cache = cache
        self._fact_store = fact_store
        self._memory_config = memory_config or {}
        self._thread_store = thread_store
        self._library_index = library_index

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

        journal_ctx, intel_ctx = self.get_combined_context(query)
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

        return AskContext(
            journal=journal_ctx,
            intel=intel_ctx,
            profile=profile_ctx,
            memory=memory_ctx,
            thoughts=thoughts_ctx,
            documents=documents_ctx,
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
            for hit in self._library_index.search(query, limit=max_items * 2, status="ready"):
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

            # Semantic search for query-relevant facts
            relevant = []
            if query:
                relevant = self._fact_store.search(query, limit=max_facts)

            # Always include high-confidence facts
            all_active = self._fact_store.get_all_active()
            high_conf_facts = [f for f in all_active if f.confidence >= high_conf]

            # Merge, dedup by ID, cap at max
            seen = set()
            merged = []
            for f in high_conf_facts + relevant:
                if f.id not in seen:
                    seen.add(f.id)
                    merged.append(f)
                if len(merged) >= max_facts:
                    break

            if not merged:
                return ""

            return self._format_memory_block(merged)
        except Exception as e:
            logger.debug("memory_context_failed", error=str(e))
            return ""

    def _format_memory_block(self, facts: list) -> str:
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

        # Group by category
        grouped: dict[str, list] = {}
        for f in facts:
            label = category_labels.get(f.category, str(f.category))
            grouped.setdefault(label, []).append(f)

        lines = ["<user_memory>"]
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
            # Sort by confidence desc within section
            for f in sorted(grouped[section], key=lambda x: x.confidence, reverse=True):
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
            import asyncio
            from datetime import datetime, timedelta

            loop = asyncio.get_event_loop()
            threads = loop.run_until_complete(self._thread_store.get_active_threads(min_entries=2))

            if not threads:
                return ""

            now = datetime.now()
            thirty_days_ago = now - timedelta(days=30)

            # Compute entries_last_30_days for sorting
            scored = []
            for t in threads:
                entries = loop.run_until_complete(self._thread_store.get_thread_entries(t.id))
                recent_count = sum(1 for e in entries if e.entry_date >= thirty_days_ago)
                first_date = min(e.entry_date for e in entries) if entries else t.created_at
                last_date = max(e.entry_date for e in entries) if entries else t.updated_at
                weeks_span = max(1, (last_date - first_date).days // 7)
                days_since_last = (now - last_date).days

                scored.append(
                    {
                        "thread": t,
                        "recent_count": recent_count,
                        "weeks_span": weeks_span,
                        "days_since_last": days_since_last,
                    }
                )

            # Sort by recent activity
            scored.sort(key=lambda x: x["recent_count"], reverse=True)
            top = scored[:max_threads]

            if not any(s["recent_count"] > 0 for s in top):
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

    def compute_dynamic_weight(self, user_id: Optional[str] = None) -> float:
        """Compute journal_weight from engagement data.

        Formula: base(0.7) + 0.15 * (journal_ratio - 0.5), clamped [0.5, 0.85].
        Returns default 0.7 when <10 events in last 30 days.
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
            return max(0.5, min(0.85, weight))
        except Exception as e:
            logger.debug("dynamic_weight_fallback", error=str(e))
            return self.journal_weight

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
        if journal_weight is not None:
            weight = journal_weight
        elif self._users_db_path and self._user_id:
            weight = self.compute_dynamic_weight()
        else:
            weight = self.journal_weight
        total_chars = self.max_context_chars
        journal_chars = int(total_chars * weight)
        intel_chars = total_chars - journal_chars

        if self.cache:
            key = self.cache.make_key("combined", query, weight=weight, total_chars=total_chars)
            cached = self.cache.get(key)
            if cached is not None:
                import json

                parts = json.loads(cached)
                return parts["journal"], parts["intel"]

        journal_ctx = self.get_journal_context(query, max_chars=journal_chars)
        intel_ctx = self.get_intel_context(query, max_chars=intel_chars)

        if self.cache:
            import json

            self.cache.set(key, json.dumps({"journal": journal_ctx, "intel": intel_ctx}))

        return journal_ctx, intel_ctx

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
