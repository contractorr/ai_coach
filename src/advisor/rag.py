"""RAG retrieval — backward-compat facade over extracted retrievers + assembler."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from advisor.context_assembler import AskContext, ContextAssembler
from advisor.retrievers.intel import IntelRetriever
from advisor.retrievers.journal import JournalRetriever
from advisor.retrievers.memory import MemoryRetriever
from advisor.retrievers.profile import ProfileRetriever
from advisor.retrievers.supplementary import SupplementaryRetriever
from intelligence.entity_store import EntityStore
from journal.search import JournalSearch

if TYPE_CHECKING:
    from advisor.entity_retriever import EntityRetriever
    from advisor.query_analyzer import QueryAnalyzer
    from advisor.query_decomposer import QueryDecomposer
    from intelligence.search import IntelSearch
    from services.reranker import CrossEncoderReranker

# Re-export AskContext for callers that import from advisor.rag
__all__ = ["AskContext", "RAGRetriever"]


class RAGRetriever:
    """Backward-compat facade over extracted retrievers + assembler."""

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
        # Build sub-retrievers
        self._profile = ProfileRetriever(profile_path or "~/coach/profile.yaml")
        self._journal = JournalRetriever(journal_search, cache)
        self._intel = IntelRetriever(
            intel_db_path, intel_search, self._profile.load, cache, user_id=user_id
        )
        # Always create MemoryRetriever (methods return "" when fact_store is None)
        self._memory = MemoryRetriever(fact_store, memory_config, thread_store)
        resolved_intel_db = Path(intel_db_path).expanduser() if intel_db_path else None
        self._supplementary = SupplementaryRetriever(
            user_id, resolved_intel_db, library_index, max_context_chars
        )

        # Build assembler
        self._assembler = ContextAssembler(
            journal=self._journal,
            intel=self._intel,
            profile=self._profile,
            memory=self._memory if fact_store else None,
            supplementary=self._supplementary,
            max_context_chars=max_context_chars,
            max_context_tokens=max_context_tokens,
            journal_weight=journal_weight,
            users_db_path=users_db_path,
            user_id=user_id,
            query_analyzer=query_analyzer,
            query_decomposer=query_decomposer,
            entity_retriever=entity_retriever,
            reranker=reranker,
            cache=cache,
        )

        # Public attrs accessed directly by callers
        self.entity_store = entity_store
        self.query_analyzer = query_analyzer
        self.query_decomposer = query_decomposer
        self.entity_retriever = entity_retriever
        self.reranker = reranker

    # ── Cache property (engine.py mutates post-construction) ─────────

    @property
    def cache(self):
        return self._assembler.cache

    @cache.setter
    def cache(self, value):
        self._journal.cache = value
        self._intel.cache = value
        self._assembler.cache = value

    # ── Mutable attributes (MCP tools mutate temporarily) ────────────

    @property
    def journal_weight(self):
        return self._assembler.journal_weight

    @journal_weight.setter
    def journal_weight(self, value):
        self._assembler.journal_weight = value

    @property
    def max_context_chars(self):
        return self._assembler.max_context_chars

    @max_context_chars.setter
    def max_context_chars(self, value):
        self._assembler.max_context_chars = value
        self._supplementary._max_context_chars = value

    @property
    def max_context_tokens(self):
        return self._assembler.max_context_tokens

    @max_context_tokens.setter
    def max_context_tokens(self, value):
        self._assembler.max_context_tokens = value

    # ── Backward-compat properties ───────────────────────────────────

    @property
    def journal(self) -> JournalSearch:
        """rag.journal → JournalSearch (test_rag.py checks this)."""
        return self._journal.search

    @property
    def search(self) -> JournalSearch:
        """rag.search.storage compat (recommendations.py:101)."""
        return self._journal.search

    @property
    def _profile_path(self) -> str:
        """rag._profile_path compat (recommendations.py:691)."""
        return self._profile._profile_path

    @_profile_path.setter
    def _profile_path(self, value: str):
        self._profile._profile_path = value

    @property
    def intel_db_path(self) -> Path | None:
        return self._intel.intel_db_path

    @property
    def intel_search(self):
        return self._intel.intel_search

    @property
    def _fact_store(self):
        return self._memory._fact_store

    @property
    def _thread_store(self):
        return self._memory._thread_store

    @property
    def _memory_config(self):
        return self._memory._memory_config

    @property
    def _users_db_path(self):
        return self._assembler._users_db_path

    @property
    def _user_id(self):
        return self._assembler._user_id

    @property
    def _library_index(self):
        return self._supplementary._library_index

    # ── Delegations — per-source retrievers ──────────────────────────

    def get_profile_context(self, *a, **kw):
        return self._profile.get_profile_context(*a, **kw)

    def get_profile_keywords(self):
        return self._profile.get_profile_keywords()

    def _load_profile(self):
        return self._profile.load()

    def _load_profile_terms(self):
        return self._profile.load_profile_terms()

    def get_journal_context(self, *a, **kw):
        return self._journal.get_journal_context(*a, **kw)

    def get_recent_entries(self, *a, **kw):
        return self._journal.get_recent_entries(*a, **kw)

    def get_research_context(self, *a, **kw):
        return self._journal.get_research_context(*a, **kw)

    def get_intel_context(self, *a, **kw):
        return self._intel.get_intel_context(*a, **kw)

    def _get_intel_context_uncached(self, *a, **kw):
        return self._intel._get_intel_context_uncached(*a, **kw)

    def get_capability_context(self):
        return self._intel.get_capability_context()

    def get_memory_context(self, *a, **kw):
        return self._memory.get_memory_context(*a, **kw)

    def _format_memory_block(self, *a, **kw):
        return self._memory._format_memory_block(*a, **kw)

    def _get_thread_fact_boosts(self):
        return self._memory._get_thread_fact_boosts()

    @staticmethod
    def _effective_fact_confidence(fact, thread_boosts):
        return MemoryRetriever._effective_fact_confidence(fact, thread_boosts)

    def get_document_context(self, *a, **kw):
        return self._supplementary.get_document_context(*a, **kw)

    def get_repo_context(self, *a, **kw):
        return self._supplementary.get_repo_context(*a, **kw)

    def get_curriculum_context(self, *a, **kw):
        return self._supplementary.get_curriculum_context(*a, **kw)

    # ── Methods kept on facade (tests mock at facade level) ──────────

    def get_recurring_thoughts_context(self, *a, **kw):
        """Delegate but bind _run_async so facade-level patches propagate."""
        saved = self._memory._run_async
        self._memory._run_async = self._run_async
        try:
            return self._memory.get_recurring_thoughts_context(*a, **kw)
        finally:
            self._memory._run_async = saved

    def get_filtered_intel_context(
        self,
        query: str,
        max_items: int = 5,
        max_chars: int = 3000,
        min_relevance: float = 0.05,
    ) -> str:
        """Facade version — calls self.get_intel_context for fallback compat."""
        if not self._intel.intel_search:
            return self.get_intel_context(query, max_items=max_items, max_chars=max_chars)
        profile_terms = self._profile.load_profile_terms()
        return self._intel.intel_search.get_filtered_context_for_query(
            query=query,
            profile_terms=profile_terms,
            max_items=max_items,
            max_chars=max_chars,
            min_relevance=min_relevance,
        )

    def get_ai_capabilities_context(self, query: str, max_chars: int = 1500) -> str:
        """Facade version — calls self.get_intel_context for mock compat."""
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

    def build_context_for_ask(
        self,
        query: str,
        rag_config: dict | None = None,
        attachment_ids: list[str] | None = None,
    ) -> AskContext:
        """Facade version — calls self.get_* so facade-level mocks work."""
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

        curriculum_ctx = ""
        if cfg.get("inject_curriculum", True):
            curriculum_ctx = self.get_curriculum_context(query)

        return AskContext(
            journal=enhanced.journal,
            intel=enhanced.intel,
            profile=profile_ctx,
            memory=memory_ctx,
            thoughts=thoughts_ctx,
            documents=documents_ctx,
            entity_context=enhanced.entity_context,
            repo_context=repo_ctx,
            curriculum_context=curriculum_ctx,
        )

    def get_full_context(
        self,
        query: str,
        include_research: bool = True,
    ) -> tuple[str, str, str]:
        """Facade version — calls self.get_combined_context + self.get_research_context."""
        journal_ctx, intel_ctx = self.get_combined_context(query)
        research_ctx = self.get_research_context(query) if include_research else ""
        return journal_ctx, intel_ctx, research_ctx

    # ── Delegations — assembler ──────────────────────────────────────

    def get_enhanced_context(self, *a, **kw):
        return self._assembler.get_enhanced_context(*a, **kw)

    def get_combined_context(self, *a, **kw):
        return self._assembler.get_combined_context(*a, **kw)

    def compute_dynamic_weight(self, *a, **kw):
        return self._assembler.compute_dynamic_weight(*a, **kw)

    # ── Delegations — budget utilities (tests call these) ────────────

    def _truncate_to_token_budget(self, journal_ctx, intel_ctx, weight):
        from advisor.context_budget import truncate_to_token_budget

        return truncate_to_token_budget(journal_ctx, intel_ctx, weight, self.max_context_tokens)

    @staticmethod
    def _truncate_lines_to_tokens(text, token_budget):
        from advisor.context_budget import truncate_lines_to_tokens

        return truncate_lines_to_tokens(text, token_budget)

    def _tokens_to_chars(self, tokens):
        from advisor.context_budget import tokens_to_chars

        return tokens_to_chars(tokens)

    # ── Async bridge compat ──────────────────────────────────────────

    @staticmethod
    def _run_async(coro):
        from advisor.async_bridge import run_async

        return run_async(coro)

    # ── Internal assembler delegations (tests may patch) ─────────────

    def _get_text_context_for_budget(self, *a, **kw):
        return self._assembler._get_text_context_for_budget(*a, **kw)

    def _get_temporal_context(self, *a, **kw):
        return self._assembler._get_temporal_context(*a, **kw)

    def _resolve_journal_weight(self, *a, **kw):
        return self._assembler._resolve_journal_weight(*a, **kw)

    def _recommendation_weight_adjustment(self, *a, **kw):
        return self._assembler._recommendation_weight_adjustment(*a, **kw)

    def _apply_reranker(self, *a, **kw):
        return self._assembler._apply_reranker(*a, **kw)

    def _merge_context_lines(self, *a, **kw):
        return self._assembler._merge_context_lines(*a, **kw)

    @staticmethod
    def _line_key(line):
        return ContextAssembler._line_key(line)
