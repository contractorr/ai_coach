"""Tests for ConflictResolver with mocked LLM."""

import json
from unittest.mock import MagicMock

import pytest

from memory.models import FactCategory, FactSource, StewardFact
from memory.resolver import ConflictResolver
from memory.store import FactStore


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "test.db"
    return FactStore(db, chroma_dir=None)


@pytest.fixture
def provider():
    return MagicMock()


@pytest.fixture
def resolver(store, provider):
    return ConflictResolver(store, provider=provider)


def _fact(id="f1", text="User prefers Python", category=FactCategory.PREFERENCE, source_id="e1"):
    return StewardFact(
        id=id,
        text=text,
        category=category,
        source_type=FactSource.JOURNAL,
        source_id=source_id,
        confidence=0.8,
    )


class TestResolve:
    def test_no_similar_returns_add(self, resolver):
        candidate = _fact(text="User likes Go")
        update = resolver.resolve_single(candidate, similar=[])
        assert update.action == "ADD"

    def test_high_similarity_auto_noop(self, resolver):
        existing = _fact(id="e1", text="User prefers Python for backend development")
        candidate = _fact(text="User prefers Python for backend development")
        update = resolver.resolve_single(candidate, similar=[existing])
        assert update.action == "NOOP"
        assert update.existing_id == "e1"

    def test_llm_returns_update(self, resolver, provider):
        provider.generate.return_value = json.dumps(
            {
                "action": "UPDATE",
                "existing_id": "e1",
                "reasoning": "Preference changed from Actix to Axum",
            }
        )
        existing = _fact(id="e1", text="User prefers Actix for Rust")
        candidate = _fact(text="User prefers Axum for Rust")
        update = resolver.resolve_single(candidate, similar=[existing])
        assert update.action == "UPDATE"
        assert update.existing_id == "e1"

    def test_llm_returns_delete(self, resolver, provider):
        provider.generate.return_value = json.dumps(
            {
                "action": "DELETE",
                "existing_id": "e1",
                "reasoning": "User explicitly stopped using Java",
            }
        )
        existing = _fact(id="e1", text="User actively uses Java")
        candidate = _fact(text="User no longer uses Java")
        update = resolver.resolve_single(candidate, similar=[existing])
        assert update.action == "DELETE"

    def test_llm_returns_add_for_distinct(self, resolver, provider):
        provider.generate.return_value = json.dumps(
            {
                "action": "ADD",
                "existing_id": None,
                "reasoning": "Different aspect of user preferences",
            }
        )
        existing = _fact(id="e1", text="User prefers Python")
        candidate = _fact(text="User prefers dark mode IDEs")
        update = resolver.resolve_single(candidate, similar=[existing])
        assert update.action == "ADD"

    def test_llm_failure_defaults_to_add(self, resolver, provider):
        provider.generate.side_effect = Exception("API error")
        existing = _fact(id="e1", text="User prefers Python")
        candidate = _fact(text="User prefers Rust now")
        update = resolver.resolve_single(candidate, similar=[existing])
        assert update.action == "ADD"

    def test_batch_resolve(self, resolver, provider):
        provider.generate.return_value = json.dumps(
            {
                "action": "ADD",
                "existing_id": None,
                "reasoning": "New fact",
            }
        )
        candidates = [
            _fact(id="c1", text="User knows SQL"),
            _fact(id="c2", text="User likes Go"),
        ]
        # Both have no similar existing facts (store is empty)
        updates = resolver.resolve(candidates)
        assert len(updates) == 2
        assert all(u.action == "ADD" for u in updates)

    def test_batch_resolve_checks_prior_batch_candidates(self, resolver, provider):
        provider.generate.return_value = json.dumps(
            {
                "action": "NOOP",
                "existing_id": None,
                "reasoning": "Same preference already captured earlier in the batch",
            }
        )
        candidates = [
            _fact(id="c1", text="User prefers Python for backend APIs"),
            _fact(id="c2", text="User prefers Python for APIs"),
        ]

        updates = resolver.resolve(candidates)

        assert [update.action for update in updates] == ["ADD", "NOOP"]
        assert updates[1].existing_id == "c1"
        provider.generate.assert_called_once()

    def test_batch_resolve_uses_fallback_search_for_paraphrases(self, resolver, provider, store):
        store.add(_fact(id="e1", text="User prefers Python for backend development"))
        provider.generate.return_value = json.dumps(
            {
                "action": "NOOP",
                "existing_id": "e1",
                "reasoning": "Same preference phrased differently",
            }
        )

        updates = resolver.resolve([_fact(id="c1", text="User prefers Python for APIs")])

        assert updates[0].action == "NOOP"
        assert updates[0].existing_id == "e1"
        provider.generate.assert_called_once()


class TestTextSimilarity:
    def test_identical(self):
        assert ConflictResolver._text_similarity("hello world", "hello world") == 1.0

    def test_no_overlap(self):
        assert ConflictResolver._text_similarity("hello world", "foo bar") == 0.0

    def test_partial(self):
        sim = ConflictResolver._text_similarity("user prefers python", "user prefers rust")
        assert 0.3 < sim < 0.8

    def test_empty(self):
        assert ConflictResolver._text_similarity("", "hello") == 0.0
