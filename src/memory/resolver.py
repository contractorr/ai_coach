"""Conflict resolution for candidate facts against existing facts."""

import json

import structlog

from .models import FactUpdate, StewardFact
from .store import FactStore

logger = structlog.get_logger()

_RESOLUTION_SYSTEM = """You resolve conflicts between a new fact and existing facts about a user.

Choose ONE action:
- ADD: The new fact is distinct from all existing facts.
- UPDATE <id>: The new fact replaces an existing fact (e.g. preference changed).
- DELETE <id>: The new fact explicitly negates an existing fact.
- NOOP: The new fact is redundant — already captured by existing facts.

Respond as JSON: {"action": "ADD|UPDATE|DELETE|NOOP", "existing_id": "<id or null>", "reasoning": "<one sentence>"}
Output ONLY JSON. No preamble."""


class ConflictResolver:
    """Compares candidate facts against existing facts to prevent contradictions."""

    def __init__(
        self,
        fact_store: FactStore,
        provider=None,
        similarity_threshold: float = 0.7,
        auto_noop_threshold: float = 0.95,
    ):
        self.store = fact_store
        self._provider = provider
        self.similarity_threshold = similarity_threshold
        self.auto_noop_threshold = auto_noop_threshold

    def _get_provider(self):
        if self._provider:
            return self._provider
        from llm.factory import create_cheap_provider

        return create_cheap_provider()

    def resolve(self, candidates: list[StewardFact]) -> list[FactUpdate]:
        """Resolve a batch of candidate facts against existing facts."""
        results = []
        for candidate in candidates:
            similar = self.store.search(candidate.text, limit=3)
            # Filter out the candidate itself if it somehow got in
            similar = [s for s in similar if s.id != candidate.id]
            update = self.resolve_single(candidate, similar)
            results.append(update)
        return results

    def resolve_single(self, candidate: StewardFact, similar: list[StewardFact]) -> FactUpdate:
        """Resolve one candidate against its similar existing facts."""
        if not similar:
            return FactUpdate(action="ADD", candidate=candidate.text)

        # Auto-NOOP if very high similarity and same category
        top = similar[0]
        if self._text_similarity(candidate.text, top.text) > self.auto_noop_threshold:
            if candidate.category == top.category:
                return FactUpdate(
                    action="NOOP",
                    candidate=candidate.text,
                    existing_id=top.id,
                    reasoning="Near-duplicate of existing fact",
                )

        # LLM resolution
        try:
            update = self._llm_resolve(candidate, similar)
            if update.action == "NOOP" and not update.existing_id and similar:
                update.existing_id = similar[0].id
            return update
        except Exception as e:
            logger.warning("conflict_resolution_failed", error=str(e))
            # Default to ADD on failure
            return FactUpdate(action="ADD", candidate=candidate.text)

    def _llm_resolve(self, candidate: StewardFact, similar: list[StewardFact]) -> FactUpdate:
        """Use LLM to resolve conflict."""
        provider = self._get_provider()

        lines = [f'New fact: "{candidate.text}" (category: {candidate.category.value})', ""]
        lines.append("Existing facts:")
        for s in similar:
            date_str = s.updated_at.strftime("%Y-%m-%d") if s.updated_at else "unknown"
            lines.append(
                f'  {s.id}: [{date_str}] "{s.text}" ({s.category.value}, confidence: {s.confidence})'
            )

        prompt = "\n".join(lines)
        response = provider.generate(
            messages=[
                {"role": "system", "content": _RESOLUTION_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
        )
        return self._parse_response(response, candidate.text)

    def _parse_response(self, response: str, candidate_text: str) -> FactUpdate:
        """Parse LLM resolution response."""
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return FactUpdate(action="ADD", candidate=candidate_text, reasoning="Parse failed")

        action = data.get("action", "ADD").upper()
        if action not in ("ADD", "UPDATE", "DELETE", "NOOP"):
            action = "ADD"

        return FactUpdate(
            action=action,
            candidate=candidate_text,
            existing_id=data.get("existing_id"),
            reasoning=data.get("reasoning", ""),
        )

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        """Cheap token-overlap similarity for auto-NOOP detection."""
        tokens_a = set(a.lower().split())
        tokens_b = set(b.lower().split())
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        return len(intersection) / len(union)
