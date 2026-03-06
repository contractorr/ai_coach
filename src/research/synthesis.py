"""Research report synthesis using LLM."""

from typing import Optional

import structlog

from cli.retry import llm_retry
from llm import LLMError, LLMRateLimitError, create_llm_provider

from .web_search import SearchResult

logger = structlog.get_logger()


class ResearchSynthesizer:
    """Synthesizes research reports from web search results."""

    SYSTEM_PROMPT = """You are a research assistant that synthesizes information from multiple sources into actionable research reports.

Your reports should be:
- Concise but comprehensive
- Focused on practical insights
- Well-structured with clear sections
- Honest about limitations or conflicting information"""

    SYNTHESIS_PROMPT = """Synthesize a research report on "{topic}" based on these sources:

{sources}

USER CONTEXT (their goals/interests):
{user_context}

Generate a research report with these sections:
## Summary
(2-3 sentence overview)

## Key Insights
(Bullet points of the most important findings)

## Relevance to Your Goals
(How this connects to the user's stated interests/goals)

## Sources
(List sources with brief descriptions)

## Next Steps
(2-3 actionable recommendations)

Be specific and practical. Cite sources when making claims."""

    DOSSIER_UPDATE_PROMPT = """You are updating an ongoing research dossier on "{topic}".

DOSSIER CONTEXT:
{dossier_context}

PREVIOUS CHANGE SUMMARY:
{previous_change_summary}

NEW SOURCES:
{sources}

USER CONTEXT:
{user_context}

Write a dossier update in markdown with exactly these sections:
## What Changed
(2-4 bullets summarizing the delta since the last update)

## Why It Matters
(1-2 short paragraphs tied to the user's goals or decisions)

## Evidence
(bullets that cite specific sources)

## Confidence
(start with High, Medium, or Low, then one sentence explaining why)

## Recommended Actions
(2-4 concrete next actions)

## Open Questions
(bullets for what still needs clarification)

## Sources
(bulleted list of sources with URLs)

Focus on what is new or changed. If little changed, say that explicitly."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        client=None,
    ):
        self.llm = create_llm_provider(
            provider=provider,
            api_key=api_key,
            model=model,
            client=client,
        )

    @llm_retry(exceptions=(LLMRateLimitError, LLMError))
    def synthesize(
        self,
        topic: str,
        results: list[SearchResult],
        user_context: str = "",
        max_tokens: int = 2000,
    ) -> str:
        """Generate research report from search results.

        Args:
            topic: Research topic
            results: Web search results
            user_context: User's goals/interests for personalization
            max_tokens: Max tokens for response

        Returns:
            Markdown-formatted research report
        """
        if not results:
            return self._empty_report(topic)

        # Format sources for prompt
        sources_text = self._format_sources(results)

        prompt = self.SYNTHESIS_PROMPT.format(
            topic=topic,
            sources=sources_text,
            user_context=user_context or "No specific context provided.",
        )

        try:
            return self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                system=self.SYSTEM_PROMPT,
                max_tokens=max_tokens,
            )
        except LLMError as e:
            logger.error("LLM synthesis failed: %s", e)
            return self._fallback_report(topic, results)

    @llm_retry(exceptions=(LLMRateLimitError, LLMError))
    def synthesize_dossier_update(
        self,
        topic: str,
        results: list[SearchResult],
        dossier_context: str,
        previous_change_summary: str = "",
        user_context: str = "",
        max_tokens: int = 1800,
    ) -> str:
        """Generate a dossier update focused on deltas since the previous run."""
        if not results:
            return self._fallback_dossier_update(topic, results, previous_change_summary)

        sources_text = self._format_sources(results)
        prompt = self.DOSSIER_UPDATE_PROMPT.format(
            topic=topic,
            dossier_context=dossier_context or "No dossier context provided.",
            previous_change_summary=previous_change_summary or "No prior update recorded.",
            sources=sources_text,
            user_context=user_context or "No specific context provided.",
        )

        try:
            return self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                system=self.SYSTEM_PROMPT,
                max_tokens=max_tokens,
            )
        except LLMError as e:
            logger.error("LLM dossier synthesis failed: %s", e)
            return self._fallback_dossier_update(topic, results, previous_change_summary)

    def _format_sources(self, results: list[SearchResult]) -> str:
        """Format search results for the prompt."""
        parts = []
        for i, r in enumerate(results, 1):
            parts.append(f"[Source {i}] {r.title}\nURL: {r.url}\nContent: {r.content}\n")
        return "\n".join(parts)

    def _empty_report(self, topic: str) -> str:
        """Generate report when no sources found."""
        return f"""## Summary
No sources found for "{topic}". This may be due to search API limitations or an overly specific query.

## Key Insights
- Unable to gather information at this time

## Next Steps
- Try a more general search term
- Check if TAVILY_API_KEY is configured correctly
- Research this topic manually"""

    def _fallback_report(self, topic: str, results: list[SearchResult]) -> str:
        """Generate basic report when LLM fails."""
        sources = "\n".join(f"- [{r.title}]({r.url})" for r in results[:5])
        return f"""## Summary
Research gathered on "{topic}" but synthesis unavailable due to API error.

## Sources Found
{sources}

## Next Steps
- Review sources manually
- Retry research later"""

    def _fallback_dossier_update(
        self,
        topic: str,
        results: list[SearchResult],
        previous_change_summary: str = "",
    ) -> str:
        """Fallback dossier update when LLM synthesis is unavailable."""
        source_lines = "\n".join(f"- {r.title}: {r.url}" for r in results[:5]) or "- No sources captured"
        prior = previous_change_summary or "No prior update recorded."
        return f"""## What Changed
- Fresh research was gathered for "{topic}", but automated delta synthesis was unavailable.
- Previous change summary: {prior}

## Why It Matters
This dossier has new source material, but the exact delta needs manual review.

## Evidence
- Review the captured sources below.

## Confidence
Low - fallback mode could not compare prior and current evidence deeply.

## Recommended Actions
- Review the latest sources manually
- Re-run dossier research later if needed

## Open Questions
- What materially changed versus the last update?

## Sources
{source_lines}
"""
