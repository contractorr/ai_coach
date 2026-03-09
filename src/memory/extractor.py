"""LLM-powered fact extraction from journal entries, feedback, goals, and documents."""

import json
import uuid
from datetime import datetime

import structlog

from .models import FactCategory, FactSource, StewardFact

logger = structlog.get_logger()

_EXTRACTION_SYSTEM = """You are a fact extraction system for a personal AI steward.

Given text, extract atomic facts about the user that would be useful for providing personalized advice.

Rules:
- Each fact must be a single sentence in third person ("User prefers...", "User is currently...")
- Only extract PERSISTENT, ACTIONABLE information. Skip:
  - Transient emotions ("had a bad day")
  - Daily logistics ("ate lunch", "went to gym")
  - Narrative filler ("it was interesting that...")
  - Vague statements without specific preferences or constraints
- Assign each fact exactly one category:
  preference: What the user likes/dislikes or how they prefer to do things
  skill: What the user knows or is capable of, and at what level
  constraint: Limitations on the user's time, energy, resources, or circumstances
  pattern: Recurring behavioral tendencies (positive or negative)
  context: Current situation, projects, or life circumstances
  goal_context: Information tied to a specific active goal
- Assign a confidence score:
  0.9-1.0: User explicitly stated this
  0.7-0.89: Strong inference from what user wrote
  0.5-0.69: Weak signal, might be reading into it
  Below 0.5: Do not extract
- Extract at most {max_facts} facts. Prioritize higher confidence facts.
- Output ONLY a JSON array. No preamble, no markdown fences.

Example output:
[
  {{"text": "User prefers Axum over Actix for Rust web APIs", "category": "preference", "confidence": 0.85}},
  {{"text": "User is more productive coding in the morning", "category": "constraint", "confidence": 0.8}}
]

If there are no extractable facts, output: []"""

_FEEDBACK_CONTEXT = """The user gave {feedback_type} feedback on a recommendation.
Recommendation: "{title}" — {description}
Extract what this feedback reveals about the user's preferences or interests."""

_GOAL_CONTEXT = """The user {event_type} a goal.
Goal: "{title}"
{extra}
Extract facts about the user's current focus, context, or aspirations."""

_DOCUMENT_CONTEXT = """The user uploaded a document for their AI steward to use.
Document title: "{title}"
Document type: {document_type}
{extra}

Extract persistent facts about the user's experience, skills, preferences, constraints, current context, or goals that are explicitly stated or strongly implied by the document."""

VALID_CATEGORIES = {c.value for c in FactCategory}


class FactExtractor:
    """Extracts atomic facts from text using an LLM."""

    def __init__(self, provider=None, max_facts_per_entry: int = 5):
        self._provider = provider
        self.max_facts = max_facts_per_entry

    def _get_provider(self):
        if self._provider:
            return self._provider
        from llm.factory import create_cheap_provider

        return create_cheap_provider()

    def extract_from_journal(
        self, entry_id: str, entry_text: str, entry_metadata: dict | None = None
    ) -> list[StewardFact]:
        """Extract facts from a journal entry."""
        if not entry_text or len(entry_text.strip()) < 20:
            return []

        system = _EXTRACTION_SYSTEM.format(max_facts=self.max_facts)
        # Truncate very long entries
        text = entry_text[:3000]
        context = ""
        if entry_metadata:
            entry_type = entry_metadata.get("type", "")
            tags = entry_metadata.get("tags", [])
            if entry_type:
                context += f"\nEntry type: {entry_type}"
            if tags:
                context += f"\nTags: {', '.join(tags)}"

        prompt = f"Journal entry:{context}\n\n{text}"
        return self._extract(system, prompt, FactSource.JOURNAL, entry_id)

    def extract_from_feedback(
        self, recommendation_id: str, feedback: str, recommendation_context: dict | None = None
    ) -> list[StewardFact]:
        """Extract preference facts from recommendation feedback."""
        ctx = recommendation_context or {}
        feedback_type = (
            "positive" if feedback in ("useful", "thumbs_up", "acted_on") else "negative"
        )
        title = ctx.get("title", "Unknown recommendation")
        description = ctx.get("description", "")[:200]

        system = _EXTRACTION_SYSTEM.format(max_facts=3)
        prompt = _FEEDBACK_CONTEXT.format(
            feedback_type=feedback_type, title=title, description=description
        )
        return self._extract(system, prompt, FactSource.FEEDBACK, recommendation_id)

    def extract_from_goal(self, goal_id: str, goal_data: dict) -> list[StewardFact]:
        """Extract context facts from goal creation or milestone completion."""
        title = goal_data.get("title", "")
        event_type = goal_data.get("event_type", "created")
        extra = ""
        if goal_data.get("milestones"):
            extra = "Milestones: " + ", ".join(
                m.get("title", "") for m in goal_data["milestones"][:5]
            )
        if goal_data.get("tags"):
            extra += f"\nTags: {', '.join(goal_data['tags'])}"

        system = _EXTRACTION_SYSTEM.format(max_facts=3)
        prompt = _GOAL_CONTEXT.format(event_type=event_type, title=title, extra=extra)
        return self._extract(system, prompt, FactSource.GOAL, goal_id)

    def extract_from_document(
        self, document_id: str, document_text: str, document_metadata: dict | None = None
    ) -> list[StewardFact]:
        """Extract durable facts from an uploaded document such as a CV."""
        if not document_text or len(document_text.strip()) < 40:
            return []

        metadata = document_metadata or {}
        title = metadata.get("title", "Uploaded document")
        document_type = metadata.get("document_type", metadata.get("mime_type", "document"))
        extra_parts = []
        if metadata.get("file_name"):
            extra_parts.append(f"File name: {metadata['file_name']}")
        if metadata.get("collection"):
            extra_parts.append(f"Collection: {metadata['collection']}")

        system = _EXTRACTION_SYSTEM.format(max_facts=self.max_facts)
        prompt = _DOCUMENT_CONTEXT.format(
            title=title,
            document_type=document_type,
            extra="\n".join(extra_parts),
        )
        prompt = f"{prompt}\n\nDocument text:\n{document_text[:5000]}"
        return self._extract(system, prompt, FactSource.DOCUMENT, document_id)

    def _extract(
        self, system: str, prompt: str, source_type: FactSource, source_id: str
    ) -> list[StewardFact]:
        """Run LLM extraction and parse results."""
        try:
            provider = self._get_provider()
            response = provider.generate(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
            )
            return self._parse_response(response, source_type, source_id)
        except Exception as e:
            logger.warning("fact_extraction_failed", source_id=source_id, error=str(e))
            return []

    def _parse_response(
        self, response: str, source_type: FactSource, source_id: str
    ) -> list[StewardFact]:
        """Parse LLM JSON response into StewardFact list."""
        text = response.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        try:
            items = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("fact_parse_failed", response=text[:200])
            return []

        if not isinstance(items, list):
            return []

        facts = []
        now = datetime.now()
        for item in items[: self.max_facts]:
            if not isinstance(item, dict):
                continue
            fact_text = item.get("text", "").strip()
            category = item.get("category", "").strip()
            confidence = item.get("confidence", 0.7)

            if not fact_text or category not in VALID_CATEGORIES:
                continue
            if not isinstance(confidence, (int, float)) or confidence < 0.5:
                continue

            facts.append(
                StewardFact(
                    id=uuid.uuid4().hex[:16],
                    text=fact_text,
                    category=FactCategory(category),
                    source_type=source_type,
                    source_id=source_id,
                    confidence=min(1.0, float(confidence)),
                    created_at=now,
                    updated_at=now,
                )
            )

        return facts
