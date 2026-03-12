"""Tests for ObservationConsolidator — entity grouping, synthesis, dedup, orphan cleanup."""

import json
from unittest.mock import MagicMock

import pytest

from memory.consolidator import ObservationConsolidator
from memory.models import FactCategory, FactSource, StewardFact
from memory.store import FactStore

_DEFAULT_JSON_RESPONSE = json.dumps(
    {
        "observation": "User is an experienced Python developer focused on data engineering.",
        "abstract": "Python data engineering experienced developer pipelines",
    }
)


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "test.db"
    return FactStore(db, chroma_dir=None)


@pytest.fixture
def provider():
    p = MagicMock()
    p.generate.return_value = _DEFAULT_JSON_RESPONSE
    return p


@pytest.fixture
def consolidator(store, provider):
    return ObservationConsolidator(store, provider=provider, min_facts_per_group=2)


def _fact(id, text, category=FactCategory.SKILL, source_id="entry-1", confidence=0.8):
    return StewardFact(
        id=id,
        text=text,
        category=category,
        source_type=FactSource.JOURNAL,
        source_id=source_id,
        confidence=confidence,
    )


class TestConsolidateAll:
    def test_two_facts_same_entity_produces_observation(self, store, consolidator, provider):
        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java", category=FactCategory.PREFERENCE))

        results = consolidator.consolidate_all()

        assert len(results) >= 1
        obs = results[0]
        assert obs.category == FactCategory.OBSERVATION
        assert obs.source_type == FactSource.CONSOLIDATION
        provider.generate.assert_called_once()

    def test_single_fact_no_observation(self, store, consolidator, provider):
        store.add(_fact("f1", "User uses Kubernetes for deployment"))

        results = consolidator.consolidate_all()

        assert len(results) == 0
        provider.generate.assert_not_called()

    def test_unchanged_facts_skip_llm(self, store, consolidator, provider):
        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))

        # First run: creates observation
        first = consolidator.consolidate_all()
        assert len(first) >= 1
        assert provider.generate.call_count == 1

        # Second run: same facts, no new LLM call
        second = consolidator.consolidate_all()
        assert len(second) >= 1
        assert provider.generate.call_count == 1  # still 1

    def test_new_fact_updates_observation(self, store, consolidator, provider):
        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))
        consolidator.consolidate_all()

        # Add new fact to same entity group
        store.add(_fact("f3", "User is learning Python async patterns"))
        provider.generate.return_value = json.dumps(
            {
                "observation": "User is an experienced Python developer advancing into async patterns.",
                "abstract": "Python async patterns experienced developer advancement",
            }
        )
        results = consolidator.consolidate_all()

        assert len(results) >= 1
        assert provider.generate.call_count == 2

    def test_observations_excluded_from_grouping(self, store, consolidator):
        """Observations themselves should not be grouped for further consolidation."""
        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))
        consolidator.consolidate_all()

        observations = store.get_all_active_observations()
        assert len(observations) >= 1
        # Observation should not appear in entity groups
        groups = consolidator._group_by_entity()
        for facts in groups.values():
            for f in facts:
                assert f.category != FactCategory.OBSERVATION


class TestConsolidateAffected:
    def test_only_affected_groups_processed(self, store, consolidator, provider):
        # Group A: Python facts
        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))
        # Group B: AWS facts (unrelated)
        store.add(_fact("f3", "User deploys on AWS Lambda"))
        store.add(_fact("f4", "User uses AWS S3 for storage"))

        consolidator.consolidate_affected(["f1"])

        # Should only process the Python group, not AWS
        assert provider.generate.call_count == 1


class TestOrphanCleanup:
    def test_source_fact_deleted_orphans_observation(self, store, consolidator):
        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))
        consolidator.consolidate_all()

        observations_before = store.get_all_active_observations()
        assert len(observations_before) >= 1

        # Delete both source facts
        store.delete("f1", reason="test")
        store.delete("f2", reason="test")

        observations_after = store.get_all_active_observations()
        assert len(observations_after) == 0


class TestLLMFailure:
    def test_llm_failure_skips_group(self, store, provider):
        provider.generate.side_effect = RuntimeError("API error")
        consolidator = ObservationConsolidator(store, provider=provider)

        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))

        results = consolidator.consolidate_all()

        assert len(results) == 0  # failed, but no crash

    def test_llm_failure_preserves_existing_observation(self, store, provider):
        consolidator = ObservationConsolidator(store, provider=provider)
        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))

        # First run succeeds
        provider.generate.return_value = json.dumps(
            {"observation": "User is a Python developer.", "abstract": "Python developer"}
        )
        consolidator.consolidate_all()
        obs_before = store.get_all_active_observations()
        assert len(obs_before) == 1

        # Add new fact, but LLM fails
        store.add(_fact("f3", "User is learning Python async"))
        provider.generate.side_effect = RuntimeError("API error")
        consolidator.consolidate_all()

        # Original observation should still be active
        obs_after = store.get_all_active_observations()
        assert len(obs_after) == 1


class TestObservationSourceLinks:
    def test_observation_links_to_source_facts(self, store, consolidator):
        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))
        results = consolidator.consolidate_all()

        assert len(results) >= 1
        obs = results[0]
        source_ids = store.get_observation_source_ids(obs.id)
        assert sorted(source_ids) == ["f1", "f2"]

    def test_get_observations_for_fact(self, store, consolidator):
        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))
        consolidator.consolidate_all()

        observations = store.get_observations_for_fact("f1")
        assert len(observations) >= 1
        assert observations[0].category == FactCategory.OBSERVATION


class TestAbstract:
    def test_abstract_stored_on_new_observation(self, store, consolidator):
        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))
        results = consolidator.consolidate_all()

        assert len(results) >= 1
        obs = results[0]
        assert obs.abstract == "Python data engineering experienced developer pipelines"
        # Verify persisted
        reloaded = store.get(obs.id)
        assert reloaded.abstract == obs.abstract

    def test_abstract_stored_on_updated_observation(self, store, consolidator, provider):
        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))
        consolidator.consolidate_all()

        store.add(_fact("f3", "User is learning Python async patterns"))
        provider.generate.return_value = json.dumps(
            {
                "observation": "User is advancing into Python async.",
                "abstract": "Python async advancement",
            }
        )
        results = consolidator.consolidate_all()
        obs = results[0]
        assert obs.abstract == "Python async advancement"

    def test_plain_text_fallback_sets_abstract_none(self, store, provider):
        """When LLM returns plain text instead of JSON, abstract should be None."""
        provider.generate.return_value = "User is a Python developer."
        consolidator = ObservationConsolidator(store, provider=provider, min_facts_per_group=2)

        store.add(_fact("f1", "User uses Python for data pipelines"))
        store.add(_fact("f2", "User prefers Python over Java"))
        results = consolidator.consolidate_all()

        assert len(results) >= 1
        obs = results[0]
        assert obs.text == "User is a Python developer."
        assert obs.abstract is None
