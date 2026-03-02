"""Unified recommendation engine."""

import asyncio
import re
from pathlib import Path
from typing import Optional

import structlog

from llm import LLMError

from .prompts import PromptTemplates
from .rag import RAGRetriever
from .recommendation_storage import Recommendation, RecommendationStorage
from .scoring import RecommendationScorer

logger = structlog.get_logger()

# Base category queries — augmented with profile keywords at runtime
CATEGORY_QUERIES = {
    "learning": "skills learning goals career development courses",
    "career": "career job role position goals ambitions work",
    "entrepreneurial": "problems frustrations ideas business startup project AI automation capabilities model",
    "investment": "technology trends funding investment market opportunity AI trends model performance benchmarks",
    "events": "conference meetup workshop event speaking cfp",
    "projects": "open source contribution project coding side-project AI tools coding assistants agents",
}

# Categories where AI capability context adds value
AI_RELEVANT_CATEGORIES = {"entrepreneurial", "projects", "investment", "learning"}

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _preprocess_llm_response(text: str) -> str:
    """Strip <think> tags from reasoning models before parsing."""
    return _THINK_RE.sub("", text).strip()


def _parse_critic_with_regex(response: str) -> dict:
    """Regex fallback when line-by-line critic parsing returns < 3 fields."""
    result = {}
    for field in ("CHALLENGE", "MISSING_CONTEXT", "ALTERNATIVE", "CONFIDENCE_RATIONALE"):
        m = re.search(rf"{field}:\s*(.+?)(?=\n[A-Z_]+:|$)", response, re.DOTALL)
        if m:
            result[field.lower()] = m.group(1).strip()
    # Confidence needs special handling (extract level keyword)
    m = re.search(r"CONFIDENCE:\s*(High|Medium|Low)", response, re.IGNORECASE)
    result["confidence"] = m.group(1).capitalize() if m else "Medium"
    return result


def _build_personalized_query(
    base_query: str, profile_keywords: list[str], max_keywords: int = 8
) -> str:
    """Augment a category query with user-specific keywords from their profile."""
    if not profile_keywords:
        return base_query
    # Deduplicate and take top keywords not already in base query
    base_lower = base_query.lower()
    unique = []
    seen = set()
    for kw in profile_keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen and kw_lower not in base_lower:
            unique.append(kw)
            seen.add(kw_lower)
            if len(unique) >= max_keywords:
                break
    if unique:
        return f"{base_query} {' '.join(unique)}"
    return base_query


class Recommender:
    """Single unified recommender that works across all categories."""

    def __init__(
        self,
        rag: RAGRetriever,
        llm_caller,
        scorer: RecommendationScorer,
        storage: RecommendationStorage,
        cheap_llm_caller=None,
    ):
        self.rag = rag
        self.llm_caller = llm_caller
        self.cheap_llm_caller = cheap_llm_caller or llm_caller
        self.scorer = scorer
        self.storage = storage

    def generate(
        self,
        category: str,
        max_items: int = 3,
        with_action_plans: bool = True,
    ) -> list[Recommendation]:
        """Generate recommendations for a category."""
        # Check for sparse data
        try:
            all_entries = self.rag.search.storage.list_entries(limit=5)
            if len(all_entries) < 5:
                logger.info(
                    "Sparse journal data (%d entries), skipping recommendations", len(all_entries)
                )
                return []
        except Exception:
            pass

        # Build profile-aware query for intel retrieval
        base_query = CATEGORY_QUERIES.get(category, category)
        profile_keywords = self.rag.get_profile_keywords()
        intel_query = _build_personalized_query(base_query, profile_keywords)

        # Get structured profile (separate from journal)
        profile_ctx = self.rag.get_profile_context(structured=True)
        journal_ctx = self.rag.get_journal_context(
            base_query,
            max_entries=8,
            max_chars=5000,
        )
        # Use profile-filtered intel retrieval (re-ranks by profile relevance)
        intel_ctx = self.rag.get_filtered_intel_context(intel_query, max_chars=3000)

        # Inject AI capability context for relevant categories
        if category in AI_RELEVANT_CATEGORIES:
            try:
                ai_ctx = self.rag.get_ai_capabilities_context(intel_query)
                # Append dynamic capability horizon model if available
                cap_ctx = self.rag.get_capability_context()
                if cap_ctx:
                    ai_ctx = f"{ai_ctx}\n\n{cap_ctx}"
                ai_section = PromptTemplates.AI_CAPABILITIES_SECTION.format(
                    ai_capabilities_context=ai_ctx,
                )
                prompt = PromptTemplates.UNIFIED_RECOMMENDATIONS_WITH_AI.format(
                    category=category,
                    profile_context=profile_ctx,
                    journal_context=journal_ctx,
                    intel_context=intel_ctx,
                    ai_capabilities_section=ai_section,
                    max_items=max_items,
                )
            except Exception as e:
                logger.warning("ai_capabilities_context_failed", error=str(e))
                prompt = PromptTemplates.UNIFIED_RECOMMENDATIONS.format(
                    category=category,
                    profile_context=profile_ctx,
                    journal_context=journal_ctx,
                    intel_context=intel_ctx,
                    max_items=max_items,
                )
        else:
            prompt = PromptTemplates.UNIFIED_RECOMMENDATIONS.format(
                category=category,
                profile_context=profile_ctx,
                journal_context=journal_ctx,
                intel_context=intel_ctx,
                max_items=max_items,
            )

        response = self.llm_caller(PromptTemplates.SYSTEM, prompt)
        recs = self._parse_recommendations(response, category)

        # === Pass 2: Adversarial critic pipeline (parallel) ===
        self._run_adversarial_pipeline_parallel(recs, profile_ctx, intel_ctx)

        if with_action_plans:
            self._run_action_plans_parallel(recs)

        return recs

    def _run_adversarial_pipeline_parallel(
        self, recs: list[Recommendation], profile_ctx: str, intel_ctx: str
    ) -> None:
        """Run adversarial pipeline in 2 waves: intel checks → critics."""
        if not recs:
            return

        async def _gather():
            # Wave 1: all intel contradiction checks in parallel
            intel_tasks = [asyncio.to_thread(self._safe_intel_check, rec) for rec in recs]
            intel_results = await asyncio.gather(*intel_tasks)

            # Wave 2: all critic calls in parallel (using wave 1 results)
            critic_tasks = [
                asyncio.to_thread(
                    self._safe_critic_apply, rec, profile_ctx, intel_ctx, intel_result
                )
                for rec, intel_result in zip(recs, intel_results)
            ]
            await asyncio.gather(*critic_tasks)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            for rec in recs:
                intel = self._safe_intel_check(rec)
                self._safe_critic_apply(rec, profile_ctx, intel_ctx, intel)
        else:
            asyncio.run(_gather())

    def _safe_intel_check(self, rec: Recommendation) -> str | None:
        try:
            return self._run_intel_contradiction_check(rec)
        except (LLMError, KeyError, ValueError) as e:
            logger.warning("intel_check_failed", title=rec.title[:50], error=str(e))
            return None

    def _safe_critic_apply(
        self,
        rec: Recommendation,
        profile_ctx: str,
        intel_ctx: str,
        intel_contradictions: str | None,
    ) -> None:
        try:
            self._apply_adversarial_critic(rec, profile_ctx, intel_ctx, intel_contradictions)
        except (LLMError, KeyError, ValueError) as e:
            logger.warning("adversarial_critic_failed", title=rec.title[:50], error=str(e))

    def _run_action_plans_parallel(self, recs: list[Recommendation]) -> None:
        """Generate action plans for high-scoring recs concurrently."""
        eligible = [r for r in recs if r.score >= 7.0]
        if not eligible:
            return

        async def _gather():
            tasks = [asyncio.to_thread(self._safe_action_plan, rec) for rec in eligible]
            await asyncio.gather(*tasks, return_exceptions=True)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            for rec in eligible:
                self._safe_action_plan(rec)
        else:
            asyncio.run(_gather())

    def _safe_action_plan(self, rec: Recommendation) -> None:
        """Generate action plan with error handling."""
        try:
            action_plan = self._generate_action_plan(rec)
            rec.metadata = rec.metadata or {}
            rec.metadata["action_plan"] = action_plan
        except (LLMError, KeyError, ValueError) as e:
            logger.warning("action_plan_failed", error=str(e))

    def _parse_recommendations(self, response: str, category: str) -> list[Recommendation]:
        """Parse LLM response into Recommendation objects."""
        recs = []
        current: dict = {}

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("### ") or line.startswith("## "):
                # Skip "Parked for later" section
                heading = line.lstrip("#").strip().lower()
                if "parked" in heading or "later" in heading:
                    if current.get("title"):
                        recs.append(self._build_recommendation(current, category))
                    current = {}
                    continue
                if current.get("title"):
                    recs.append(self._build_recommendation(current, category))
                current = {"title": line.lstrip("#").strip()}
            elif (
                line.startswith("**Why you, specifically**:")
                or line.startswith("**Why**:")
                or line.startswith("RATIONALE:")
            ):
                current["rationale"] = line.split(":", 1)[-1].strip()
            elif (
                line.startswith("**What**:")
                or line.startswith("**Description**:")
                or line.startswith("DESCRIPTION:")
            ):
                current["description"] = line.split(":", 1)[-1].strip()
            elif line.startswith("**Intel trigger**:"):
                current["intel_trigger"] = line.split(":", 1)[-1].strip()
            elif line.startswith("**Pre-mortem**:"):
                current["premortem"] = line.split(":", 1)[-1].strip()
            elif line.startswith("**Next step**:"):
                current["next_step"] = line.split(":", 1)[-1].strip()
            elif line.startswith("RELEVANCE:"):
                try:
                    current["relevance"] = min(
                        10.0, max(0.0, float(line.split(":")[-1].strip().split()[0]))
                    )
                except (ValueError, IndexError):
                    pass
            elif line.startswith("FEASIBILITY:"):
                try:
                    current["feasibility"] = min(
                        10.0, max(0.0, float(line.split(":")[-1].strip().split()[0]))
                    )
                except (ValueError, IndexError):
                    pass
            elif line.startswith("IMPACT:"):
                try:
                    current["impact"] = min(
                        10.0, max(0.0, float(line.split(":")[-1].strip().split()[0]))
                    )
                except (ValueError, IndexError):
                    pass
            elif line.startswith("SCORE:"):
                try:
                    current["score"] = min(
                        10.0, max(0.0, float(line.split(":")[-1].strip().split()[0]))
                    )
                except (ValueError, IndexError):
                    current["score"] = 5.0
            elif line.startswith("SOURCE:") or line.startswith("- SOURCE:"):
                current["reasoning_source"] = line.split(":", 1)[-1].strip()
            elif line.startswith("PROFILE_MATCH:") or line.startswith("- PROFILE_MATCH:"):
                current["reasoning_profile_match"] = line.split(":", 1)[-1].strip()
            elif line.startswith("CONFIDENCE:") or line.startswith("- CONFIDENCE:"):
                try:
                    current["reasoning_confidence"] = min(
                        1.0, max(0.0, float(line.split(":", 1)[-1].strip()))
                    )
                except ValueError:
                    current["reasoning_confidence"] = 0.5
            elif line.startswith("CAVEATS:") or line.startswith("- CAVEATS:"):
                current["reasoning_caveats"] = line.split(":", 1)[-1].strip()
            elif current.get("title") and not current.get("description") and line:
                current["description"] = current.get("description", "") + " " + line

        if current.get("title"):
            recs.append(self._build_recommendation(current, category))

        # Filter by threshold and dedupe
        valid = []
        for rec in recs:
            if self.scorer.passes_threshold(rec.score):
                content_hash = self.scorer.content_hash(rec.title, rec.description)
                if not self.storage.hash_exists(content_hash):
                    rec.embedding_hash = content_hash
                    valid.append(rec)

        return valid

    def _build_recommendation(self, data: dict, category: str) -> Recommendation:
        metadata = {}
        reasoning_trace = {}
        if data.get("reasoning_source"):
            reasoning_trace["source_signal"] = data["reasoning_source"]
        if data.get("reasoning_profile_match"):
            reasoning_trace["profile_match"] = data["reasoning_profile_match"]
        if "reasoning_confidence" in data:
            reasoning_trace["confidence"] = data["reasoning_confidence"]
        if data.get("reasoning_caveats"):
            reasoning_trace["caveats"] = data["reasoning_caveats"]
        if reasoning_trace:
            metadata["reasoning_trace"] = reasoning_trace

        # Store disaggregated scores
        sub_scores = {}
        if "relevance" in data:
            sub_scores["relevance"] = data["relevance"]
        if "feasibility" in data:
            sub_scores["feasibility"] = data["feasibility"]
        if "impact" in data:
            sub_scores["impact"] = data["impact"]
        if sub_scores:
            metadata["sub_scores"] = sub_scores

        # Store intel trigger, premortem, and next step if present
        if data.get("intel_trigger"):
            metadata["intel_trigger"] = data["intel_trigger"]
        if data.get("premortem"):
            metadata["premortem"] = data["premortem"]
        if data.get("next_step"):
            metadata["next_step"] = data["next_step"]

        # Compute weighted score from sub-scores if available, else use raw
        if all(k in data for k in ("relevance", "feasibility", "impact")):
            raw_score = 0.5 * data["relevance"] + 0.2 * data["feasibility"] + 0.3 * data["impact"]
        else:
            raw_score = data.get("score", 5.0)
        adjusted = self.scorer.adjust_score(raw_score, category)

        return Recommendation(
            category=category,
            title=data.get("title", ""),
            description=data.get("description", "").strip(),
            rationale=data.get("rationale", ""),
            score=adjusted,
            metadata=metadata or None,
        )

    def _apply_adversarial_critic(
        self,
        rec: Recommendation,
        profile_ctx: str,
        intel_ctx: str,
        intel_contradictions: str | None,
    ) -> None:
        """Apply intel contradictions + adversarial critic to a recommendation.

        Mutates rec.metadata in place to add critic fields.
        Intel check already done in wave 1; this handles metadata + critic call.
        """
        rec.metadata = rec.metadata or {}
        premortem = rec.metadata.get("premortem", "None provided")

        if intel_contradictions:
            rec.metadata["intel_contradictions"] = intel_contradictions

        critic = self._run_adversarial_critic(
            rec, profile_ctx, intel_ctx, premortem, intel_contradictions
        )
        if critic:
            rec.metadata["confidence"] = critic.get("confidence", "Medium")
            rec.metadata["confidence_rationale"] = critic.get("confidence_rationale", "")
            rec.metadata["critic_challenge"] = critic.get("challenge", "")
            rec.metadata["missing_context"] = critic.get("missing_context", "")
            alt = critic.get("alternative")
            rec.metadata["alternative"] = alt if alt and alt.lower() != "null" else None

            # Update reasoning_trace confidence to match critic assessment
            trace = rec.metadata.get("reasoning_trace", {})
            confidence_map = {"high": 0.85, "medium": 0.55, "low": 0.25}
            trace["confidence"] = confidence_map.get(
                rec.metadata["confidence"].lower(), trace.get("confidence", 0.5)
            )
            rec.metadata["reasoning_trace"] = trace

    def _run_intel_contradiction_check(self, rec: Recommendation) -> str | None:
        """Check recent intel for contradictions to a recommendation."""
        # Get broad recent intel (not profile-filtered — we want contradictions)
        recent_intel = self.rag.get_intel_context(
            f"{rec.title} {rec.category}",
            max_items=8,
            max_chars=3000,
        )
        if not recent_intel or "No" in recent_intel[:15]:
            return None

        prompt = PromptTemplates.INTEL_CONTRADICTION_CHECK.format(
            title=rec.title,
            description=rec.description,
            rationale=rec.rationale,
            recent_intel=recent_intel,
        )

        response = self.cheap_llm_caller(PromptTemplates.SYSTEM, prompt, max_tokens=600)
        response = _preprocess_llm_response(response)

        # Parse verdict
        verdict = ""
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("VERDICT:"):
                verdict = line.split(":", 1)[-1].strip().upper()

        if verdict in ("SUPPORTED", ""):
            return None

        # Return the full response for contradicted/complicated cases
        return response

    def _run_adversarial_critic(
        self,
        rec: Recommendation,
        profile_ctx: str,
        intel_ctx: str,
        premortem: str,
        intel_contradictions: str | None,
    ) -> dict | None:
        """Run adversarial critic on a recommendation."""
        prompt = PromptTemplates.ADVERSARIAL_CRITIC.format(
            profile_context=profile_ctx,
            title=rec.title,
            description=rec.description,
            rationale=rec.rationale,
            premortem=premortem,
            intel_summary=intel_ctx[:2000],
            intel_contradictions=intel_contradictions or "No contradictions found in live intel.",
        )

        response = self.cheap_llm_caller(PromptTemplates.SYSTEM, prompt, max_tokens=800)
        response = _preprocess_llm_response(response)

        # Parse structured response (line-by-line)
        result = {}
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("CHALLENGE:"):
                result["challenge"] = line.split(":", 1)[-1].strip()
            elif line.startswith("MISSING_CONTEXT:"):
                result["missing_context"] = line.split(":", 1)[-1].strip()
            elif line.startswith("ALTERNATIVE:"):
                result["alternative"] = line.split(":", 1)[-1].strip()
            elif line.startswith("CONFIDENCE:"):
                val = line.split(":", 1)[-1].strip()
                # Extract just High/Medium/Low from potentially longer text
                for level in ("High", "Medium", "Low"):
                    if level.lower() in val.lower():
                        result["confidence"] = level
                        break
                else:
                    result["confidence"] = "Medium"
            elif line.startswith("CONFIDENCE_RATIONALE:"):
                result["confidence_rationale"] = line.split(":", 1)[-1].strip()

        # Regex fallback if line-by-line parsing got < 3 fields
        if len(result) < 3:
            logger.debug("critic_line_parse_sparse", fields=len(result), falling_back="regex")
            result = _parse_critic_with_regex(response)
            if "challenge" not in result or "confidence" not in result:
                logger.warning("critic_parse_incomplete", fields=list(result.keys()))

        return result if result else None

    def _generate_action_plan(self, rec: Recommendation) -> str:
        profile_ctx = self.rag.get_profile_context()
        journal_ctx = self.rag.get_journal_context(
            f"{rec.title} {rec.category}",
            max_entries=5,
            max_chars=2000,
        )
        prompt = PromptTemplates.ACTION_PLAN.format(
            title=rec.title,
            category=rec.category,
            description=rec.description,
            rationale=rec.rationale,
            journal_context=profile_ctx + journal_ctx,
        )
        return self.llm_caller(PromptTemplates.SYSTEM, prompt, max_tokens=1000)


class RecommendationEngine:
    """Orchestrates recommendation generation."""

    def __init__(
        self,
        rag: RAGRetriever,
        llm_caller,
        storage: RecommendationStorage,
        config: Optional[dict] = None,
        users_db_path: Optional[Path] = None,
        user_id: Optional[str] = None,
        cheap_llm_caller=None,
        intel_db_path: Optional[Path] = None,
    ):
        self.rag = rag
        self.llm_caller = llm_caller
        self.cheap_llm_caller = cheap_llm_caller or llm_caller
        self.storage = storage
        self.config = config or {}

        self._prediction_store = None
        if intel_db_path:
            try:
                from predictions.store import PredictionStore

                self._prediction_store = PredictionStore(intel_db_path)
            except Exception:
                pass

        scoring_config = self.config.get("scoring", {})
        self.scorer = RecommendationScorer(
            min_threshold=scoring_config.get("min_threshold", 6.0),
            users_db_path=users_db_path,
            user_id=user_id,
            intel_db_path=intel_db_path,
            rec_storage=storage,
        )

        self.recommender = Recommender(
            rag, llm_caller, self.scorer, storage, cheap_llm_caller=self.cheap_llm_caller
        )

        # Determine enabled categories
        categories = self.config.get("categories", {})
        self.enabled_categories = [cat for cat in CATEGORY_QUERIES if categories.get(cat, True)]

    def generate_category(
        self,
        category: str,
        max_items: int = 3,
        save: bool = True,
        with_action_plans: bool = True,
    ) -> list[Recommendation]:
        """Generate recommendations for a single category."""
        if category not in CATEGORY_QUERIES:
            logger.warning("Unknown category: %s", category)
            return []

        recs = self.recommender.generate(
            category,
            max_items=max_items,
            with_action_plans=with_action_plans,
        )

        if save:
            for rec in recs:
                rec.id = self.storage.save(rec)
                try:
                    from predictions.recorder import record_from_recommendation

                    record_from_recommendation(rec, self._prediction_store)
                except Exception:
                    pass

        return recs

    def generate_all(
        self,
        max_per_category: int = 3,
        save: bool = True,
        with_action_plans: bool = True,
    ) -> dict[str, list[Recommendation]]:
        """Generate recommendations for all enabled categories."""
        results = {}
        for category in self.enabled_categories:
            results[category] = self.generate_category(
                category,
                max_items=max_per_category,
                save=save,
                with_action_plans=with_action_plans,
            )
        return results

    def get_top_recommendations(
        self,
        limit: int = 5,
        min_score: float = 6.0,
    ) -> list[Recommendation]:
        """Get top recommendations across all categories."""
        return self.storage.get_top_by_score(
            min_score=min_score,
            limit=limit,
            exclude_status=["completed", "dismissed"],
        )

    def generate_top_picks(
        self,
        max_picks: int = 5,
        min_score: float = 6.0,
        pool_size: int = 15,
    ) -> str:
        """Select top picks across all categories using LLM consolidation.

        Gathers the best recommendations from storage, then asks the LLM
        to rank and select the most important actions for this week.

        Returns:
            Markdown-formatted top picks with justification.
        """
        # Get pool of candidates
        candidates = self.storage.get_top_by_score(
            min_score=min_score,
            limit=pool_size,
            exclude_status=["completed", "dismissed"],
        )

        if not candidates:
            return "No recommendations available. Generate some first with `coach recommend all`."

        if len(candidates) <= max_picks:
            # Not enough to warrant consolidation
            lines = [f"# Top {len(candidates)} Picks This Week\n"]
            for i, rec in enumerate(candidates, 1):
                lines.append(f"### {i}. [{rec.category.upper()}] {rec.title}")
                lines.append(f"Score: {rec.score:.1f} — {rec.description[:200]}")
                if rec.rationale:
                    lines.append(f"Why: {rec.rationale[:200]}")
                lines.append("")
            return "\n".join(lines)

        # Format candidates for prompt
        rec_lines = []
        for rec in candidates:
            sub = rec.metadata.get("sub_scores", {}) if rec.metadata else {}
            score_detail = f"SCORE: {rec.score:.1f}"
            if sub:
                score_detail += f" (R:{sub.get('relevance', '?')} F:{sub.get('feasibility', '?')} I:{sub.get('impact', '?')})"
            rec_lines.append(
                f"- [{rec.category.upper()}] {rec.title} — {score_detail}\n"
                f"  {rec.description[:200]}\n"
                f"  Why: {rec.rationale[:200] if rec.rationale else 'N/A'}"
            )
        all_rec_text = "\n\n".join(rec_lines)

        # Get profile for context
        profile_ctx = self.rag.get_profile_context(structured=True)

        # Get weekly hours from profile
        weekly_hours = 5
        try:
            from profile.storage import ProfileStorage

            ps = ProfileStorage(self.rag._profile_path)
            profile = ps.load()
            if profile:
                weekly_hours = profile.constraints.get(
                    "time_per_week", profile.weekly_hours_available
                )
        except Exception:
            pass

        prompt = PromptTemplates.TOP_PICKS.format(
            profile_context=profile_ctx,
            all_recommendations=all_rec_text,
            max_picks=max_picks,
            rank="{rank}",  # literal for template
            category="{category}",
            title="{title}",
            original_score="{original_score}",
            weekly_hours=weekly_hours,
        )

        top_picks_text = self.llm_caller(PromptTemplates.SYSTEM, prompt)

        # Contrarianism check on #1 pick only
        # COST NOTE: 1 additional LLM call per top-picks generation
        top_rec = candidates[0]  # highest-scored rec
        try:
            contrarian_result = self._run_top_pick_contrarian(top_rec, profile_ctx)
            if contrarian_result:
                top_picks_text += f"\n\n---\n{contrarian_result}"
        except (LLMError, KeyError, ValueError) as e:
            logger.warning("top_pick_contrarian_failed", error=str(e))

        return top_picks_text

    def _run_top_pick_contrarian(self, rec: Recommendation, profile_ctx: str) -> str | None:
        """Run contrarianism check on the top pick."""
        meta = rec.metadata or {}
        recent_intel = self.rag.get_intel_context(
            f"{rec.title} {rec.category}", max_items=5, max_chars=2000
        )

        prompt = PromptTemplates.TOP_PICK_CONTRARIAN.format(
            profile_context=profile_ctx,
            title=rec.title,
            description=rec.description,
            rationale=rec.rationale,
            critic_challenge=meta.get("critic_challenge", "No critic challenge available"),
            recent_intel=recent_intel,
        )

        response = self.cheap_llm_caller(PromptTemplates.SYSTEM, prompt, max_tokens=600)

        # Parse FLIP field
        flip = False
        for line in response.split("\n"):
            if line.strip().startswith("FLIP:"):
                flip = "YES" in line.upper()
                break

        if flip:
            return f"### Contrarian check — top pick flipped\n{response}"
        return None  # original stands, no additional text
