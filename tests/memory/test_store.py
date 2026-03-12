"""Tests for FactStore — CRUD, search, soft-delete, history chain."""

import pytest

from memory.models import FactCategory, FactSource, StewardFact
from memory.store import FactStore


@pytest.fixture
def store(tmp_path):
    """FactStore with SQLite only (no ChromaDB for fast tests)."""
    db = tmp_path / "test.db"
    return FactStore(db, chroma_dir=None)


def _fact(
    id="f1",
    text="User prefers Python",
    category=FactCategory.PREFERENCE,
    source_id="entry-1",
    confidence=0.85,
):
    return StewardFact(
        id=id,
        text=text,
        category=category,
        source_type=FactSource.JOURNAL,
        source_id=source_id,
        confidence=confidence,
    )


class TestAddAndRetrieve:
    def test_add_and_get(self, store):
        f = _fact()
        store.add(f)
        result = store.get("f1")
        assert result is not None
        assert result.text == "User prefers Python"
        assert result.category == FactCategory.PREFERENCE

    def test_get_nonexistent(self, store):
        assert store.get("nonexistent") is None

    def test_get_all_active(self, store):
        store.add(_fact(id="a"))
        store.add(_fact(id="b", text="User knows Rust", category=FactCategory.SKILL))
        facts = store.get_all_active()
        assert len(facts) == 2

    def test_get_by_source(self, store):
        store.add(_fact(id="a", source_id="entry-1"))
        store.add(_fact(id="b", source_id="entry-2"))
        facts = store.get_by_source(FactSource.JOURNAL, "entry-1")
        assert len(facts) == 1
        assert facts[0].id == "a"

    def test_get_by_category(self, store):
        store.add(_fact(id="a", category=FactCategory.PREFERENCE))
        store.add(_fact(id="b", category=FactCategory.SKILL, text="User knows SQL"))
        prefs = store.get_by_category(FactCategory.PREFERENCE)
        assert len(prefs) == 1
        assert prefs[0].id == "a"


class TestUpdateCreatesSupersessionChain:
    def test_update(self, store):
        store.add(_fact(id="old"))
        new = store.update("old", "User prefers Rust now", "entry-2")
        assert new.text == "User prefers Rust now"
        assert new.id != "old"

        old = store.get("old")
        assert old.superseded_by == new.id

    def test_update_nonexistent_raises(self, store):
        with pytest.raises(ValueError):
            store.update("nonexistent", "text", "src")

    def test_superseded_excluded_from_active(self, store):
        store.add(_fact(id="old"))
        store.update("old", "User prefers Rust now", "entry-2")
        active = store.get_all_active()
        assert all(f.id != "old" for f in active)
        assert len(active) == 1

    def test_update_decays_old_confidence_before_superseding(self, store):
        store.add(_fact(id="old", confidence=0.9))
        new = store.update("old", "User prefers Rust now", "entry-2", new_confidence=0.95)

        old = store.get("old")
        assert old is not None
        assert old.confidence == pytest.approx(0.75)
        assert old.superseded_by == new.id
        assert new.confidence == pytest.approx(0.95)

    def test_update_can_replace_source_type_and_category(self, store):
        store.add(_fact(id="old"))

        new = store.update(
            "old",
            "User is preparing for interviews",
            "doc-1",
            new_source_type=FactSource.DOCUMENT,
            new_category=FactCategory.CONTEXT,
        )

        assert new.source_type == FactSource.DOCUMENT
        assert new.source_id == "doc-1"
        assert new.category == FactCategory.CONTEXT


class TestDelete:
    def test_soft_delete(self, store):
        store.add(_fact(id="d1"))
        store.delete("d1", reason="test")
        fact = store.get("d1")
        assert fact.superseded_by == "DELETED:test"

    def test_deleted_excluded_from_active(self, store):
        store.add(_fact(id="d1"))
        store.delete("d1")
        assert store.get_all_active() == []

    def test_delete_by_source(self, store):
        store.add(_fact(id="a", source_id="entry-1"))
        store.add(_fact(id="b", source_id="entry-1"))
        store.add(_fact(id="c", source_id="entry-2"))
        deleted = store.delete_by_source(FactSource.JOURNAL, "entry-1")
        assert deleted == 2
        active = store.get_all_active()
        assert len(active) == 1
        assert active[0].id == "c"

    def test_delete_decays_confidence_before_soft_delete(self, store):
        store.add(_fact(id="d1", confidence=0.8))
        store.delete("d1", reason="test")
        fact = store.get("d1")
        assert fact is not None
        assert fact.confidence == pytest.approx(0.65)
        assert fact.superseded_by == "DELETED:test"


class TestConfidenceLifecycle:
    def test_reinforce_caps_at_one(self, store):
        store.add(_fact(id="r1", confidence=0.98))
        updated = store.reinforce("r1")
        assert updated is not None
        assert updated.confidence == pytest.approx(1.0)


class TestSearch:
    def test_keyword_search(self, store):
        store.add(_fact(id="a", text="User prefers Python for backend"))
        store.add(_fact(id="b", text="User knows Rust systems programming"))
        results = store.search("Python", limit=5)
        assert len(results) == 1
        assert results[0].id == "a"

    def test_search_with_category(self, store):
        store.add(_fact(id="a", text="User prefers Python", category=FactCategory.PREFERENCE))
        store.add(_fact(id="b", text="User knows Python", category=FactCategory.SKILL))
        results = store.search("Python", limit=5, categories=[FactCategory.SKILL])
        assert len(results) == 1
        assert results[0].category == FactCategory.SKILL

    def test_search_excludes_superseded(self, store):
        store.add(_fact(id="old", text="User prefers Java"))
        store.update("old", "User prefers Python now", "entry-2")
        results = store.search("prefers", limit=5)
        # Should only find the new version
        assert all("Java" not in r.text for r in results)

    def test_fallback_search_surfaces_paraphrase_matches(self, store):
        store.add(_fact(id="a", text="User prefers Python for backend development"))
        store.add(_fact(id="b", text="User prefers Java for enterprise systems"))

        results = store.search("User prefers Python for APIs", limit=5)

        assert results
        assert results[0].id == "a"


class TestHistory:
    def test_history_chain(self, store):
        store.add(_fact(id="v1", text="User prefers Java"))
        new = store.update("v1", "User prefers Kotlin", "e2")
        history = store.get_history(new.id)
        assert len(history) == 2
        assert history[0].id == "v1"
        assert history[1].id == new.id

    def test_history_single(self, store):
        store.add(_fact(id="solo"))
        history = store.get_history("solo")
        assert len(history) == 1


class TestStats:
    def test_stats(self, store):
        store.add(_fact(id="a", category=FactCategory.PREFERENCE))
        store.add(_fact(id="b", category=FactCategory.SKILL, text="knows SQL"))
        store.add(_fact(id="c", category=FactCategory.PREFERENCE, text="likes Rust"))
        stats = store.get_stats()
        assert stats["total_active"] == 3
        assert stats["by_category"]["preference"] == 2
        assert stats["by_category"]["skill"] == 1

    def test_stats_excludes_superseded(self, store):
        store.add(_fact(id="old"))
        store.update("old", "new text", "e2")
        stats = store.get_stats()
        assert stats["total_active"] == 1
        assert stats["total_superseded"] == 1


class TestGraphExpansion:
    def test_entity_links_created_on_add(self, store):
        store.add(_fact(id="e1", text="User uses Machine Learning with AWS"))
        from db import wal_connect

        with wal_connect(store.db_path) as conn:
            links = conn.execute(
                "SELECT * FROM fact_entity_links WHERE fact_id = ?", ("e1",)
            ).fetchall()
            entities = conn.execute("SELECT * FROM fact_entities").fetchall()
        assert len(links) > 0
        assert len(entities) > 0

    def test_graph_expands_to_entity_neighbors(self, store):
        # Two facts share "Python" entity
        store.add(_fact(id="g1", text="User builds Django with Python"))
        store.add(_fact(id="g2", text="User prefers Python over Ruby"))
        # Search for Django — should also find g2 via shared Python entity
        results = store.search("Django", limit=5, use_graph=True)
        result_ids = {r.id for r in results}
        assert "g1" in result_ids
        assert "g2" in result_ids

    def test_graph_disabled_with_use_graph_false(self, store):
        store.add(_fact(id="g1", text="User builds Django with Python"))
        store.add(_fact(id="g2", text="User prefers Python over Ruby"))
        results = store.search("Django", limit=5, use_graph=False)
        result_ids = {r.id for r in results}
        assert "g1" in result_ids
        # g2 should NOT appear — no keyword match for "Django"
        assert "g2" not in result_ids

    def test_entity_links_cleaned_on_delete(self, store):
        store.add(_fact(id="d1", text="User uses AWS for ML projects"))
        store.delete("d1", reason="test")
        from db import wal_connect

        with wal_connect(store.db_path) as conn:
            links = conn.execute(
                "SELECT * FROM fact_entity_links WHERE fact_id = ?", ("d1",)
            ).fetchall()
        assert len(links) == 0

    def test_superseded_not_returned_as_neighbor(self, store):
        store.add(_fact(id="s1", text="User uses Python for ML"))
        store.add(_fact(id="s2", text="User builds Python APIs"))
        # Supersede s2
        store.update("s2", "User builds Rust APIs", "entry-3")
        # Search for ML — s2 was superseded, should not appear as neighbor
        results = store.search("ML", limit=5, use_graph=True)
        result_ids = {r.id for r in results}
        assert "s2" not in result_ids

    def test_backfill_entity_links(self, store):
        # Add facts, then manually clear entity links to simulate legacy state
        store.add(_fact(id="b1", text="User uses AWS Lambda"))
        store.add(_fact(id="b2", text="User prefers GCP Cloud"))
        from db import wal_connect

        with wal_connect(store.db_path) as conn:
            conn.execute("DELETE FROM fact_entity_links")

        # Backfill should re-index both
        count = store.backfill_entity_links()
        assert count == 2

        with wal_connect(store.db_path) as conn:
            links = conn.execute("SELECT * FROM fact_entity_links").fetchall()
        assert len(links) > 0

    def test_no_entities_in_text(self, store):
        # All lowercase, no entities — should not crash
        store.add(_fact(id="n1", text="user prefers simple tools"))
        from db import wal_connect

        with wal_connect(store.db_path) as conn:
            links = conn.execute(
                "SELECT * FROM fact_entity_links WHERE fact_id = ?", ("n1",)
            ).fetchall()
        assert len(links) == 0
        # Search should still work
        results = store.search("simple tools", limit=5)
        assert len(results) >= 1


class TestGetFactsForEntity:
    def test_returns_matching_active_facts(self, store):
        store.add(_fact(id="e1", text="User builds Django with Python"))
        store.add(_fact(id="e2", text="User prefers Python over Ruby"))
        results = store.get_facts_for_entity("python")
        assert len(results) >= 1
        assert all("Python" in f.text for f in results)

    def test_excludes_superseded_facts(self, store):
        store.add(_fact(id="e1", text="User uses Python for ML"))
        store.update("e1", "User uses Rust for ML", "entry-2")
        results = store.get_facts_for_entity("python")
        assert all(f.id != "e1" for f in results)

    def test_returns_empty_for_unknown_entity(self, store):
        store.add(_fact(id="e1", text="User prefers Python"))
        results = store.get_facts_for_entity("haskell")
        assert results == []

    def test_respects_limit(self, store):
        for i in range(10):
            store.add(_fact(id=f"e{i}", text=f"User uses Python for project {i}"))
        results = store.get_facts_for_entity("python", limit=3)
        assert len(results) <= 3


class TestObservationSources:
    def test_link_and_get_observation_sources(self, store):
        store.add(_fact(id="obs1", category=FactCategory.PREFERENCE))
        store.add(_fact(id="f1"))
        store.add(_fact(id="f2"))

        store.link_observation_sources("obs1", ["f1", "f2"])
        source_ids = store.get_observation_source_ids("obs1")
        assert sorted(source_ids) == ["f1", "f2"]

    def test_get_observations_for_fact(self, store):
        from memory.models import FactSource

        obs = StewardFact(
            id="obs1",
            text="User is a Python expert",
            category=FactCategory.OBSERVATION,
            source_type=FactSource.CONSOLIDATION,
            source_id="python",
            confidence=0.85,
        )
        store.add(obs)
        store.add(_fact(id="f1"))
        store.link_observation_sources("obs1", ["f1"])

        observations = store.get_observations_for_fact("f1")
        assert len(observations) == 1
        assert observations[0].id == "obs1"

    def test_get_all_active_observations(self, store):
        from memory.models import FactSource

        obs = StewardFact(
            id="obs1",
            text="User is a Python expert",
            category=FactCategory.OBSERVATION,
            source_type=FactSource.CONSOLIDATION,
            source_id="python",
        )
        store.add(obs)
        store.add(_fact(id="f1"))

        observations = store.get_all_active_observations()
        assert len(observations) == 1
        assert observations[0].category == FactCategory.OBSERVATION

    def test_delete_cleans_observation_sources(self, store):
        store.add(_fact(id="f1"))
        store.add(_fact(id="obs1", category=FactCategory.PREFERENCE))
        store.link_observation_sources("obs1", ["f1"])

        store.delete("f1", reason="test")

        from db import wal_connect

        with wal_connect(store.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM observation_sources WHERE fact_id = ?", ("f1",)
            ).fetchall()
        assert len(rows) == 0


class TestReset:
    def test_reset(self, store):
        store.add(_fact(id="a"))
        store.add(_fact(id="b"))
        count = store.reset()
        assert count == 2
        assert store.get_all_active() == []

    def test_reset_clears_entity_tables(self, store):
        store.add(_fact(id="a", text="User uses AWS for ML"))
        store.reset()
        from db import wal_connect

        with wal_connect(store.db_path) as conn:
            entities = conn.execute("SELECT COUNT(*) FROM fact_entities").fetchone()[0]
            links = conn.execute("SELECT COUNT(*) FROM fact_entity_links").fetchone()[0]
        assert entities == 0
        assert links == 0

    def test_reset_clears_observation_sources(self, store):
        store.add(_fact(id="f1"))
        store.add(_fact(id="obs1"))
        store.link_observation_sources("obs1", ["f1"])
        store.reset()

        from db import wal_connect

        with wal_connect(store.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM observation_sources").fetchone()[0]
        assert count == 0


class TestParentScorePropagation:
    """Tests for Phase 2: parent-score propagation via entity groups."""

    def test_get_fact_entities(self, store):
        store.add(_fact(id="p1", text="User builds Django with Python"))
        store.add(_fact(id="p2", text="User prefers Python over Ruby"))
        entity_map = store._get_fact_entities({"p1", "p2"})
        # Both should have entity links
        assert "p1" in entity_map
        assert "p2" in entity_map
        assert len(entity_map["p1"]) > 0

    def test_get_fact_entities_empty(self, store):
        result = store._get_fact_entities(set())
        assert result == {}

    def test_propagate_high_score_seed_boosts_neighbors(self, store):
        """Neighbor of a high-embedding-score seed should rank above neighbor of a low-score seed."""
        # Seed facts with different "embedding scores"
        f1 = _fact(id="h1", text="User excels at Python programming")
        f2 = _fact(id="h2", text="User tried Ruby once")
        f3 = _fact(id="h3", text="User builds Python ML pipelines")  # neighbor of h1 via Python
        f4 = _fact(id="h4", text="User reads Ruby blogs")  # neighbor of h2 via Ruby
        for f in [f1, f2, f3, f4]:
            store.add(f)

        # Simulate scored seeds: h1 highly relevant, h2 marginal
        scored_seeds = [(f1, 0.95), (f2, 0.3)]
        results = store._propagate_and_merge(scored_seeds, limit=10, graph_limit=5)
        result_ids = [r.id for r in results]

        # h3 (Python neighbor of high-score h1) should rank above h4 (Ruby neighbor of low-score h2)
        assert "h3" in result_ids
        assert "h4" in result_ids
        assert result_ids.index("h3") < result_ids.index("h4")

    def test_propagate_seeds_rescored_with_group(self, store):
        """Seeds are re-scored with α-blended group scores, not just embedding."""
        f1 = _fact(id="s1", text="User uses Python for ML")
        f2 = _fact(id="s2", text="User builds Python APIs")
        store.add(f1)
        store.add(f2)

        # Both share Python entity; f1 higher embedding score
        scored_seeds = [(f1, 0.9), (f2, 0.4)]
        results = store._propagate_and_merge(scored_seeds, limit=10, graph_limit=5, alpha=0.5)
        # f2 should get boosted by Python group (driven by f1's 0.9)
        # f2 final = 0.5 * 0.4 + 0.5 * 0.9 = 0.65
        # f1 final = 0.5 * 0.9 + 0.5 * 0.9 = 0.9
        # f1 still first but f2 boosted
        assert results[0].id == "s1"
        assert len(results) == 2

    def test_alpha_one_pure_embedding(self, store):
        """alpha=1.0 should produce pure embedding score ordering."""
        f1 = _fact(id="a1", text="User uses Python for ML")
        f2 = _fact(id="a2", text="User uses Python for APIs")
        store.add(f1)
        store.add(f2)

        scored_seeds = [(f1, 0.3), (f2, 0.9)]
        results = store._propagate_and_merge(scored_seeds, limit=10, graph_limit=5, alpha=1.0)
        # Pure embedding: f2 (0.9) before f1 (0.3)
        assert results[0].id == "a2"
        assert results[1].id == "a1"

    def test_alpha_zero_pure_group(self, store):
        """alpha=0.0 should produce pure group score ordering."""
        f1 = _fact(id="z1", text="User uses Python for ML")
        f2 = _fact(id="z2", text="User uses Ruby for scripting")
        f3 = _fact(id="z3", text="User builds Python web apps")  # neighbor via Python
        store.add(f1)
        store.add(f2)
        store.add(f3)

        # f1 has high embedding, shares Python with f3
        scored_seeds = [(f1, 0.95), (f2, 0.1)]
        results = store._propagate_and_merge(scored_seeds, limit=10, graph_limit=5, alpha=0.0)
        result_ids = [r.id for r in results]
        # f1 and f3 share Python group (score=0.95), f2 has Ruby group (score=0.1)
        # With alpha=0, f2 final = 0.1, f1 final = 0.95, f3 final = 0.95
        assert "z3" in result_ids
        # f2 should be last (lowest group score)
        assert result_ids[-1] == "z2"

    def test_observation_boosts_source_facts(self, store):
        """Observation matching query should boost its source facts."""
        from memory.models import FactSource

        # Source facts
        f1 = _fact(id="of1", text="User uses Python daily")
        f2 = _fact(id="of2", text="User builds Django apps")
        store.add(f1)
        store.add(f2)

        # Observation linked to f1 and f2
        obs = StewardFact(
            id="obs1",
            text="User is a Python and Django expert",
            category=FactCategory.OBSERVATION,
            source_type=FactSource.CONSOLIDATION,
            source_id="python",
            confidence=0.85,
        )
        store.add(obs)
        store.link_observation_sources("obs1", ["of1", "of2"])

        # Observation as a high-scoring seed
        scored_seeds = [(obs, 0.9)]
        results = store._propagate_and_merge(scored_seeds, limit=10, graph_limit=5)
        result_ids = [r.id for r in results]

        # Source facts should appear via observation propagation
        assert "of1" in result_ids
        assert "of2" in result_ids

    def test_no_entities_falls_back_to_embedding_order(self, store):
        """Facts with no extractable entities should rank by embedding score."""
        f1 = _fact(id="ne1", text="user likes simple tools")  # no entities (lowercase)
        f2 = _fact(id="ne2", text="user prefers minimal code")
        store.add(f1)
        store.add(f2)

        scored_seeds = [(f1, 0.3), (f2, 0.8)]
        results = store._propagate_and_merge(scored_seeds, limit=10, graph_limit=5)
        # No entities → no group boost → alpha * emb + (1-alpha) * 0
        # f2: 0.5 * 0.8 = 0.4, f1: 0.5 * 0.3 = 0.15
        assert results[0].id == "ne2"

    def test_search_alpha_param_accepted(self, store):
        """search() should accept alpha parameter without error."""
        store.add(_fact(id="sa1", text="User uses Python"))
        # keyword fallback path (no ChromaDB) — alpha ignored but shouldn't crash
        results = store.search("Python", limit=5, alpha=0.7)
        assert len(results) >= 1

    def test_keyword_fallback_unchanged(self, store):
        """Keyword path still uses _graph_expand_and_merge, not propagation."""
        store.add(_fact(id="kf1", text="User builds Django with Python"))
        store.add(_fact(id="kf2", text="User prefers Python over Ruby"))
        results = store.search("Django", limit=5, use_graph=True)
        result_ids = {r.id for r in results}
        # Graph expansion still works via old RRF path
        assert "kf1" in result_ids
        assert "kf2" in result_ids


class TestAbstract:
    def test_add_and_get_preserves_abstract(self, store):
        f = _fact(id="abs1")
        f.abstract = "Python preference backend development"
        store.add(f)
        result = store.get("abs1")
        assert result.abstract == "Python preference backend development"

    def test_abstract_defaults_to_none(self, store):
        store.add(_fact(id="abs2"))
        result = store.get("abs2")
        assert result.abstract is None

    def test_update_with_new_abstract(self, store):
        store.add(_fact(id="abs3"))
        new = store.update(
            "abs3",
            "User prefers Rust now",
            "entry-2",
            new_abstract="Rust preference migration systems programming",
        )
        assert new.abstract == "Rust preference migration systems programming"
        reloaded = store.get(new.id)
        assert reloaded.abstract == "Rust preference migration systems programming"

    def test_update_without_abstract_defaults_none(self, store):
        f = _fact(id="abs4")
        f.abstract = "old abstract"
        store.add(f)
        new = store.update("abs4", "User prefers Rust", "entry-2")
        assert new.abstract is None
