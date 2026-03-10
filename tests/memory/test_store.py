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


class TestReset:
    def test_reset(self, store):
        store.add(_fact(id="a"))
        store.add(_fact(id="b"))
        count = store.reset()
        assert count == 2
        assert store.get_all_active() == []
