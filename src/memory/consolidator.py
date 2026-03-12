"""Observation consolidation — synthesize raw facts into higher-level observations."""

import json

import structlog

from .models import FactCategory, FactSource, StewardFact
from .store import FactStore

logger = structlog.get_logger()

_SYNTHESIS_PROMPT = """You synthesize memory observations from individual facts about a user.

Given these facts about "{entity_name}":
{fact_list}

Output a JSON object with two fields:
1. "observation" — ONE sentence capturing the overall pattern. Start with "User...", preserve contradictions as evolution.
2. "abstract" — A keyword-dense phrase (under 40 words) optimized for semantic search. Include key entities, skills, tools, and relationships. No articles or filler words.

Example output:
{{"observation": "User has transitioned from Java to Kotlin for Android development while maintaining Java for backend services.", "abstract": "Java Kotlin Android development transition backend services mobile native"}}

Output ONLY the JSON object. No preamble."""


class ObservationConsolidator:
    """Groups related facts by entity and synthesizes observations via LLM."""

    def __init__(
        self,
        store: FactStore,
        provider=None,
        min_facts_per_group: int = 2,
    ):
        self.store = store
        self._provider = provider
        self.min_facts_per_group = min_facts_per_group

    @property
    def provider(self):
        if self._provider is None:
            from llm import create_cheap_provider

            self._provider = create_cheap_provider()
        return self._provider

    def consolidate_affected(self, fact_ids: list[str]) -> list[StewardFact]:
        """Incremental: consolidate only entity groups containing given fact_ids."""
        all_groups = self._group_by_entity()
        # Find groups that contain any of the affected facts
        affected_groups = {}
        affected_set = set(fact_ids)
        for entity_key, facts in all_groups.items():
            if any(f.id in affected_set for f in facts):
                affected_groups[entity_key] = facts

        results = []
        for entity_key, facts in affected_groups.items():
            obs = self._synthesize(entity_key, facts)
            if obs:
                results.append(obs)
        return results

    def consolidate_all(self) -> list[StewardFact]:
        """Full pass: consolidate every qualifying entity group."""
        groups = self._group_by_entity()
        results = []
        for entity_key, facts in groups.items():
            obs = self._synthesize(entity_key, facts)
            if obs:
                results.append(obs)
        return results

    def _group_by_entity(self) -> dict[str, list[StewardFact]]:
        """Group active non-observation facts by their linked entity."""
        from db import wal_connect

        groups: dict[str, list[StewardFact]] = {}

        with wal_connect(self.store.db_path) as conn:
            rows = conn.execute("""
                SELECT fe.normalized, l.fact_id
                FROM fact_entity_links l
                JOIN fact_entities fe ON l.entity_id = fe.id
                JOIN steward_facts f ON l.fact_id = f.id
                WHERE f.superseded_by IS NULL AND f.category != 'observation'
            """).fetchall()

        # Build entity -> fact_id mapping
        entity_fact_ids: dict[str, list[str]] = {}
        for normalized, fact_id in rows:
            entity_fact_ids.setdefault(normalized, []).append(fact_id)

        # Filter by min size and resolve to StewardFact objects
        for entity_key, fact_ids in entity_fact_ids.items():
            unique_ids = list(dict.fromkeys(fact_ids))  # preserve order, dedup
            if len(unique_ids) < self.min_facts_per_group:
                continue
            facts = []
            for fid in unique_ids:
                fact = self.store.get(fid)
                if fact and fact.superseded_by is None:
                    facts.append(fact)
            if len(facts) >= self.min_facts_per_group:
                groups[entity_key] = facts

        return groups

    def _synthesize(self, entity_key: str, facts: list[StewardFact]) -> StewardFact | None:
        """Synthesize an observation for an entity group. Skips if unchanged."""
        fact_ids = sorted(f.id for f in facts)

        # Check for existing observation covering this entity
        existing_obs = self._find_existing_observation(entity_key)
        if existing_obs:
            existing_source_ids = sorted(self.store.get_observation_source_ids(existing_obs.id))
            if existing_source_ids == fact_ids:
                return existing_obs  # no change, skip LLM call

        # Build prompt
        fact_list = "\n".join(f"{i + 1}. {f.text}" for i, f in enumerate(facts))
        prompt = _SYNTHESIS_PROMPT.format(entity_name=entity_key, fact_list=fact_list)

        try:
            response = self.provider.generate(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            ).strip()
        except Exception as e:
            logger.warning(
                "consolidation_llm_failed",
                entity=entity_key,
                error=str(e),
            )
            return None

        if not response:
            return None

        # Parse structured JSON; fallback to plain text for backward compat
        try:
            parsed = json.loads(response)
            observation_text = parsed["observation"]
            if not isinstance(observation_text, str):
                raise ValueError("observation must be string")
            observation_text = observation_text.strip()
            abstract_raw = parsed.get("abstract", "")
            abstract_text = (
                abstract_raw.strip()
                if isinstance(abstract_raw, str) and abstract_raw.strip()
                else None
            )
        except (json.JSONDecodeError, KeyError, AttributeError, ValueError):
            observation_text = response
            abstract_text = None

        avg_confidence = sum(f.confidence for f in facts) / len(facts)

        if existing_obs:
            # Update: supersede old observation, create new
            new_obs = self.store.update(
                existing_obs.id,
                observation_text,
                entity_key,
                new_source_type=FactSource.CONSOLIDATION,
                new_category=FactCategory.OBSERVATION,
                new_confidence=avg_confidence,
                decay_amount=0.0,
                new_abstract=abstract_text,
            )
        else:
            # Create new observation
            new_obs = StewardFact(
                id="",
                text=observation_text,
                category=FactCategory.OBSERVATION,
                source_type=FactSource.CONSOLIDATION,
                source_id=entity_key,
                confidence=avg_confidence,
                abstract=abstract_text,
            )
            new_obs = self.store.add(new_obs)

        # Link source facts
        self.store.link_observation_sources(new_obs.id, fact_ids)
        logger.info(
            "observation_consolidated",
            entity=entity_key,
            observation_id=new_obs.id,
            source_count=len(fact_ids),
        )
        return new_obs

    def _find_existing_observation(self, entity_key: str) -> StewardFact | None:
        """Find active observation for an entity key (stored as source_id)."""
        facts = self.store.get_by_source(FactSource.CONSOLIDATION, entity_key)
        for f in facts:
            if f.superseded_by is None and f.category == FactCategory.OBSERVATION:
                return f
        return None
