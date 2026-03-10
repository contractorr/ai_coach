"""LLM orchestration for advice generation."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import structlog

from llm import LLMError as BaseLLMError
from llm import LLMRateLimitError, create_cheap_provider, create_llm_provider

from .action_brief import ActionBriefGenerator
from .agentic import AgenticOrchestrator
from .context_cache import ContextCache
from .council import CouncilMember, CouncilOrchestrator, is_council_eligible
from .goals import GoalTracker
from .prompts import PromptTemplates
from .rag import RAGRetriever
from .recommendation_storage import RecommendationStorage
from .recommendations import RecommendationEngine
from .tools import build_tool_registry

logger = structlog.get_logger()

# Retry decorator for LLM calls
try:
    from retry_utils import llm_retry

    _llm_retry = llm_retry(
        max_attempts=3,
        min_wait=2.0,
        max_wait=30.0,
        exceptions=(LLMRateLimitError, BaseLLMError),
    )
except ImportError:

    def _llm_retry(func):
        return func


class AdvisorError(Exception):
    """Base exception for advisor errors."""

    pass


class APIKeyMissingError(AdvisorError):
    """Raised when API key is not configured."""

    pass


class LLMError(AdvisorError):
    """Raised when LLM call fails."""

    pass


@dataclass
class AdviceResult:
    answer: str
    council_used: bool = False
    council_member_count: int = 0
    council_providers: list[str] = field(default_factory=list)
    council_failed_providers: list[str] = field(default_factory=list)
    council_partial: bool = False


class AdvisorEngine:
    """Main advisor engine using pluggable LLM providers."""

    def __init__(
        self,
        rag: RAGRetriever,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        client=None,  # Dependency injection for testing
        use_tools: bool = False,
        components: Optional[dict] = None,
        rag_config: dict | None = None,
        council_members: list[CouncilMember] | None = None,
        council_enabled: bool = True,
        council_lead_provider: str | None = None,
        council_provider_factory: Callable[..., object] | None = None,
    ):
        self.rag = rag
        self.model = model
        self.use_tools = use_tools
        self._rag_config = rag_config or {}
        self._council_members = council_members or []
        self._council_enabled = council_enabled
        self._council_lead_provider = council_lead_provider or provider
        self._council_provider_factory = council_provider_factory or create_llm_provider

        # Attach context cache to RAG if not already set
        if not getattr(rag, "cache", None):
            try:
                cache_path = Path("~/coach/context_cache.db").expanduser()
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                rag.cache = ContextCache(cache_path)
            except Exception:
                pass  # non-critical

        try:
            self.llm = create_llm_provider(
                provider=provider,
                api_key=api_key,
                model=model,
                client=client,
            )
            self.cheap_llm = create_cheap_provider(
                provider=provider,
                api_key=api_key,
                client=client,
            )
        except BaseLLMError as e:
            raise APIKeyMissingError(str(e)) from e

        self._orchestrator = None
        if use_tools and components:
            registry = build_tool_registry(components)

            # Build coaching prompt with active goals summary
            goals_summary = ""
            try:
                storage = components.get("storage")
                if storage:
                    tracker = GoalTracker(storage)
                    goals = tracker.get_goals(include_inactive=False)
                    lines = []
                    for g in goals[:8]:
                        status = g.get("status", "active")
                        progress = tracker.get_progress(Path(g["path"]))
                        pct = progress.get("percent", 0)
                        stale = " [STALE]" if g.get("is_stale") else ""
                        fname = Path(g["path"]).name
                        lines.append(f"- {g['title']} ({status}, {pct}% done{stale}) — {fname}")
                    if lines:
                        goals_summary = "\n".join(lines)
            except Exception:
                pass  # broken goals must not prevent startup

            system_prompt = PromptTemplates.build_agentic_system(goals_summary)

            # When profile is missing/empty, pre-inject journal context so
            # the LLM has user context even if it doesn't call search tools.
            profile_ctx = rag.get_profile_context()
            if not profile_ctx.strip():
                try:
                    journal_ctx = rag.get_recent_entries(days=30, max_chars=3000)
                    if journal_ctx.strip():
                        system_prompt += (
                            "\n\nNOTE: No user profile found yet. Here are their recent "
                            "journal entries for context — use these to personalize your advice:\n"
                            + journal_ctx
                        )
                except Exception:
                    pass

            self._orchestrator = AgenticOrchestrator(
                llm=self.llm,
                registry=registry,
                system_prompt=system_prompt,
                cheap_llm=self.cheap_llm,
            )

    @_llm_retry
    def _call_llm(
        self,
        system: str,
        user_prompt: str,
        max_tokens: int = 2000,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """Make LLM API call with retry on transient errors."""
        try:
            logger.debug("Calling LLM provider=%s tokens=%d", self.llm.provider_name, max_tokens)
            messages = list(conversation_history or [])
            messages.append({"role": "user", "content": user_prompt})
            return self.llm.generate(
                messages=messages,
                system=system,
                max_tokens=max_tokens,
            )
        except BaseLLMError as e:
            logger.error("LLM call failed: %s", e)
            raise LLMError(str(e)) from e

    @_llm_retry
    def _call_cheap_llm(
        self,
        system: str,
        user_prompt: str,
        max_tokens: int = 2000,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """Make LLM call using cheap-tier model for critic/background tasks."""
        try:
            logger.debug("Calling cheap LLM provider=%s", self.cheap_llm.provider_name)
            messages = list(conversation_history or [])
            messages.append({"role": "user", "content": user_prompt})
            return self.cheap_llm.generate(
                messages=messages,
                system=system,
                max_tokens=max_tokens,
            )
        except BaseLLMError as e:
            logger.error("Cheap LLM call failed: %s", e)
            raise LLMError(str(e)) from e

    def ask(
        self,
        question: str,
        advice_type: str = "general",
        include_research: bool = True,
        conversation_history: list[dict] | None = None,
        attachment_ids: list[str] | None = None,
        event_callback: Callable[[dict], None] | None = None,
    ) -> str:
        return self.ask_result(
            question,
            advice_type=advice_type,
            include_research=include_research,
            conversation_history=conversation_history,
            attachment_ids=attachment_ids,
            event_callback=event_callback,
        ).answer

    def _build_advice_prompt(
        self,
        question: str,
        advice_type: str,
        include_research: bool,
        attachment_ids: list[str] | None,
    ) -> tuple[str, str]:
        """Build the shared advisor prompt used by both single-provider and council flows."""
        if advice_type == "skill_gap":
            profile_ctx = self.rag.get_profile_context()
            journal_ctx = self.rag.get_journal_context(
                question or "skills goals career aspirations learning",
                max_entries=8,
                max_chars=4000,
            )
            prompt = PromptTemplates.SKILL_GAP_ANALYSIS.format(
                profile_context=profile_ctx,
                journal_context=journal_ctx,
                question=question or "What are my skill gaps?",
            )
            return PromptTemplates.SYSTEM, prompt

        use_extended = any(
            self._rag_config.get(k, False)
            for k in (
                "structured_profile",
                "inject_memory",
                "inject_recurring_thoughts",
                "inject_documents",
                "xml_delimiters",
            )
        ) or bool(attachment_ids)

        research_ctx = ""
        if include_research and hasattr(self.rag, "get_research_context"):
            research_ctx = self.rag.get_research_context(question)
        has_research = bool(research_ctx.strip())
        enhanced_ctx = self.rag.get_enhanced_context(question)
        system_prompt = PromptTemplates.SYSTEM
        if enhanced_ctx.entity_context:
            system_prompt += "\n\n" + PromptTemplates.ENTITY_SYSTEM_SUFFIX

        if use_extended:
            ctx = self.rag.build_context_for_ask(
                question,
                self._rag_config,
                attachment_ids=attachment_ids,
            )
            prompt_template = PromptTemplates.get_prompt(
                advice_type,
                with_research=has_research,
                xml_delimiters=self._rag_config.get("xml_delimiters", False),
                extended=True,
            )
            user_prompt = PromptTemplates._build_user_prompt(
                template=prompt_template,
                journal_context=ctx.journal,
                intel_context=ctx.intel,
                profile_context=ctx.profile,
                documents_context=ctx.documents,
                memory_context=ctx.memory,
                thoughts_context=ctx.thoughts,
                research_context=research_ctx if has_research else "",
                entity_context=ctx.entity_context,
                question=question,
            )
            return system_prompt, user_prompt

        profile_ctx = self.rag.get_profile_context()
        prompt_template = PromptTemplates.get_prompt(advice_type, with_research=has_research)
        user_prompt = prompt_template.format(
            journal_context=profile_ctx + enhanced_ctx.journal,
            intel_context=enhanced_ctx.intel,
            research_context=research_ctx if has_research else "",
            entity_context=enhanced_ctx.entity_context,
            question=question,
        )
        return system_prompt, user_prompt

    def _should_use_council(self, question: str, advice_type: str) -> bool:
        return (
            self._council_enabled
            and len(self._council_members) >= 2
            and is_council_eligible(question, advice_type=advice_type)
        )

    def ask_result(
        self,
        question: str,
        advice_type: str = "general",
        include_research: bool = True,
        conversation_history: list[dict] | None = None,
        attachment_ids: list[str] | None = None,
        event_callback: Callable[[dict], None] | None = None,
    ) -> AdviceResult:
        """Get advice for a question.

        Args:
            question: User's question
            advice_type: general, career, goals, opportunities, skill_gap
            include_research: Include deep research context
            conversation_history: Prior conversation messages for context
            event_callback: Optional callback for streaming events

        Returns:
            LLM-generated advice
        """
        if self._should_use_council(question, advice_type):
            system_prompt, user_prompt = self._build_advice_prompt(
                question,
                advice_type,
                include_research,
                attachment_ids,
            )
            if event_callback:
                event_callback(
                    {
                        "type": "council_start",
                        "providers": [member.provider for member in self._council_members],
                    }
                )
            council_result = CouncilOrchestrator(
                members=self._council_members,
                lead_provider=self._council_lead_provider,
                provider_factory=self._council_provider_factory,
            ).run(
                system=system_prompt,
                user_prompt=user_prompt,
                conversation_history=conversation_history,
            )
            if event_callback:
                event_callback(
                    {
                        "type": "council_done",
                        "providers": council_result.providers,
                        "failed_providers": council_result.failed_providers,
                        "used": council_result.used,
                    }
                )
            return AdviceResult(
                answer=council_result.answer,
                council_used=council_result.used,
                council_member_count=len(council_result.providers),
                council_providers=council_result.providers,
                council_failed_providers=council_result.failed_providers,
                council_partial=council_result.partial,
            )

        # Agentic mode: LLM decides what to look up via tool calls
        if self._orchestrator and not attachment_ids:
            return AdviceResult(
                answer=self._orchestrator.run(
                    question,
                    conversation_history=conversation_history,
                    event_callback=event_callback,
                )
            )
        system_prompt, user_prompt = self._build_advice_prompt(
            question,
            advice_type,
            include_research,
            attachment_ids,
        )
        return AdviceResult(
            answer=self._call_llm(
                system_prompt,
                user_prompt,
                conversation_history=conversation_history,
            )
        )

    def weekly_review(self, journal_storage=None) -> str:
        """Generate weekly review from recent entries.

        Args:
            journal_storage: Optional storage for stale goal detection
        """
        journal_ctx = self.rag.get_recent_entries(days=7)
        intel_ctx = self.rag.get_intel_context("weekly industry trends", max_chars=2000)

        # Add stale goals warning if storage provided
        stale_goals_ctx = ""
        if journal_storage:
            tracker = GoalTracker(journal_storage)
            stale = tracker.get_stale_goals()
            if stale:
                stale_goals_ctx = "\n\nSTALE GOALS NEEDING ATTENTION:\n"
                for g in stale[:5]:
                    stale_goals_ctx += (
                        f"- {g['title']} (last check: {g.get('days_since_check', '?')} days ago)\n"
                    )

        # Recurring thought threads
        recurring_ctx = self.rag.get_recurring_thoughts_context()

        profile_ctx = self.rag.get_profile_context()
        prompt = PromptTemplates.WEEKLY_REVIEW.format(
            journal_context=profile_ctx + journal_ctx + stale_goals_ctx + recurring_ctx,
            intel_context=intel_ctx,
        )

        return self._call_llm(PromptTemplates.SYSTEM, prompt, max_tokens=1500)

    def detect_opportunities(self) -> str:
        """Identify opportunities based on profile and trends."""
        # Use broad query to get diverse journal context
        journal_ctx = self.rag.get_journal_context(
            "skills interests goals projects work",
            max_entries=8,
            max_chars=5000,
        )
        intel_ctx = self.rag.get_intel_context(
            "opportunities trends hiring funding",
            max_chars=3000,
        )

        profile_ctx = self.rag.get_profile_context()
        prompt = PromptTemplates.OPPORTUNITY_DETECTION.format(
            journal_context=profile_ctx + journal_ctx,
            intel_context=intel_ctx,
        )

        return self._call_llm(PromptTemplates.SYSTEM, prompt)

    def analyze_goals(self, specific_goal: Optional[str] = None) -> str:
        """Analyze goal progress."""
        query = specific_goal or "goals objectives targets plans"
        journal_ctx = self.rag.get_journal_context(query, max_chars=6000)

        prompt = PromptTemplates.GOAL_ANALYSIS.format(
            journal_context=journal_ctx,
            question=specific_goal or "How am I progressing on my goals?",
        )

        return self._call_llm(PromptTemplates.SYSTEM, prompt)

    def generate_milestones(
        self,
        goal_path: Path,
        journal_storage=None,
    ) -> list[str]:
        """Auto-generate milestones for a goal via cheap LLM.

        Args:
            goal_path: Path to goal file
            journal_storage: Optional storage for reading goal content

        Returns:
            List of milestone title strings added to the goal

        Raises:
            ValueError: If goal not found
        """
        import re

        import frontmatter as fm

        if not goal_path.exists():
            raise ValueError(f"Goal not found: {goal_path}")

        post = fm.load(goal_path)
        goal_title = post.metadata.get("title", "Untitled Goal")
        goal_type = post.metadata.get("goal_type", "general")
        goal_content = post.content[:2000] if post.content else ""

        profile_context = self.rag.get_profile_context()

        prompt = PromptTemplates.MILESTONE_GENERATION.format(
            goal_title=goal_title,
            goal_type=goal_type,
            goal_content=goal_content,
            profile_context=profile_context,
        )

        try:
            response = self._call_cheap_llm(PromptTemplates.SYSTEM, prompt, max_tokens=500)
        except LLMError:
            logger.warning("generate_milestones.llm_failed", goal=str(goal_path))
            return []

        # Parse numbered list
        titles = []
        for line in response.strip().splitlines():
            m = re.match(r"^\d+\.\s+(.+)$", line.strip())
            if m:
                titles.append(m.group(1).strip())

        if not titles:
            logger.warning("generate_milestones.parse_failed", goal=str(goal_path))
            return []

        tracker = GoalTracker(journal_storage) if journal_storage else None
        added = []
        for title in titles:
            if tracker:
                tracker.add_milestone(goal_path, title)
            else:
                # Direct frontmatter manipulation if no storage
                post = fm.load(goal_path)
                milestones = post.metadata.get("milestones", [])
                milestones.append({"title": title, "completed": False, "completed_at": None})
                post["milestones"] = milestones
                with open(goal_path, "w") as f:
                    f.write(fm.dumps(post))
            added.append(title)

        return added

    # === Recommendation Methods ===

    def _get_rec_storage(self, rec_path: Path):
        """Lazy init recommendation storage."""
        return RecommendationStorage(rec_path)

    def _get_rec_engine(self, db_path: Path, config: Optional[dict] = None):
        """Lazy init recommendation engine."""
        storage = self._get_rec_storage(db_path)
        return RecommendationEngine(
            rag=self.rag,
            llm_caller=self._call_llm,
            storage=storage,
            config=config,
            cheap_llm_caller=self._call_cheap_llm,
            intel_db_path=getattr(self.rag, "intel_db_path", None),
        )

    def generate_recommendations(
        self,
        category: str,
        db_path: Path,
        config: Optional[dict] = None,
        max_items: int = 3,
    ) -> list:
        """Generate recommendations for a category.

        Args:
            category: learning, career, entrepreneurial, investment, or all
            db_path: Path to recommendations database
            config: Recommendation config
            max_items: Max items per category

        Returns:
            List of Recommendation objects
        """
        engine = self._get_rec_engine(db_path, config)

        if category == "all":
            results = engine.generate_all(max_per_category=max_items)
            # Flatten to single list
            all_recs = []
            for recs in results.values():
                all_recs.extend(recs)
            return sorted(all_recs, key=lambda r: r.score, reverse=True)
        else:
            return engine.generate_category(category, max_items=max_items)

    def generate_action_brief(
        self,
        db_path: Path,
        journal_storage=None,
        max_items: int = 5,
        min_score: float = 6.0,
        save: bool = False,
    ) -> str:
        """Generate weekly action brief.

        Args:
            db_path: Path to recommendations database
            journal_storage: Optional storage to save brief
            max_items: Max recommendations to include
            min_score: Minimum score threshold
            save: Save as journal entry

        Returns:
            Action brief markdown
        """
        storage = self._get_rec_storage(db_path)
        generator = ActionBriefGenerator(
            rag=self.rag,
            llm_caller=self._call_llm,
            rec_storage=storage,
            journal_storage=journal_storage,
        )

        if save and journal_storage:
            filepath = generator.generate_and_save(
                max_items=max_items,
                min_score=min_score,
            )
            logger.info("Saved action brief to %s", filepath)

        return generator.generate(max_items=max_items, min_score=min_score)
