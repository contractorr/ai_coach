"""Tests for MemoryPipeline — integration of extract -> resolve -> store."""

import json
from unittest.mock import MagicMock

import pytest

from memory.extractor import FactExtractor
from memory.models import FactCategory, FactSource
from memory.pipeline import MemoryPipeline
from memory.resolver import ConflictResolver
from memory.store import FactStore


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "test.db"
    return FactStore(db, chroma_dir=None)


@pytest.fixture
def provider():
    p = MagicMock()
    # Default: extract returns facts, resolver auto-ADDs (no similar found)
    p.generate.return_value = json.dumps(
        [
            {"text": "User prefers Python", "category": "preference", "confidence": 0.85},
        ]
    )
    return p


@pytest.fixture
def pipeline(store, provider):
    extractor = FactExtractor(provider=provider)
    resolver = ConflictResolver(store, provider=provider)
    return MemoryPipeline(store, extractor, resolver)


class TestJournalPipeline:
    def test_end_to_end(self, pipeline, store):
        updates = pipeline.process_journal_entry(
            "entry-1",
            "I really prefer Python for backend work. It's my go-to language.",
        )
        assert len(updates) == 1
        assert updates[0].action == "ADD"

        facts = store.get_all_active()
        assert len(facts) == 1
        assert facts[0].text == "User prefers Python"

    def test_empty_entry(self, pipeline, store):
        updates = pipeline.process_journal_entry("entry-1", "")
        assert updates == []
        assert store.get_all_active() == []

    def test_llm_returns_no_facts(self, pipeline, provider, store):
        provider.generate.return_value = "[]"
        updates = pipeline.process_journal_entry(
            "entry-1", "Just a normal day, nothing special happened at all."
        )
        assert updates == []

    def test_repeated_fact_reinforces_existing_confidence(self, pipeline, provider, store):
        provider.generate.return_value = json.dumps(
            [
                {"text": "User prefers Python", "category": "preference", "confidence": 0.85},
            ]
        )

        first = pipeline.process_journal_entry("entry-1", "Python is still my default choice.")
        second = pipeline.process_journal_entry(
            "entry-2", "I still prefer Python for backend work."
        )

        assert first[0].action == "ADD"
        assert second[0].action == "NOOP"

        facts = store.get_all_active()
        assert len(facts) == 1
        assert facts[0].confidence == pytest.approx(0.9)

    def test_duplicate_fact_text_in_one_batch_does_not_crash(self, pipeline, provider, store):
        provider.generate.return_value = json.dumps(
            [
                {"text": "User prefers Python", "category": "preference", "confidence": 0.85},
                {"text": "User prefers Python", "category": "preference", "confidence": 0.8},
            ]
        )

        updates = pipeline.process_journal_entry(
            "entry-1",
            "I prefer Python for backend work and keep coming back to Python for backend work.",
        )

        assert [update.action for update in updates] == ["ADD", "ADD"]
        facts = store.get_all_active()
        assert len(facts) == 2
        assert [fact.text for fact in facts] == ["User prefers Python", "User prefers Python"]


class TestFeedbackPipeline:
    def test_feedback_stores_fact(self, pipeline, store, provider):
        provider.generate.return_value = json.dumps(
            [
                {
                    "text": "User not interested in Java",
                    "category": "preference",
                    "confidence": 0.75,
                },
            ]
        )
        updates = pipeline.process_feedback(
            "rec-1",
            "thumbs_down",
            {"title": "Learn Java", "description": "Tutorial"},
        )
        assert len(updates) == 1
        facts = store.get_all_active()
        assert len(facts) == 1
        assert facts[0].source_type == FactSource.FEEDBACK


class TestGoalPipeline:
    def test_goal_event(self, pipeline, store, provider):
        provider.generate.return_value = json.dumps(
            [
                {"text": "User learning Rust", "category": "goal_context", "confidence": 0.95},
            ]
        )
        updates = pipeline.process_goal_event(
            "goal-1", "created", {"title": "Learn Rust", "tags": ["rust"]}
        )
        assert len(updates) == 1
        facts = store.get_all_active()
        assert len(facts) == 1
        assert facts[0].category == FactCategory.GOAL_CONTEXT


class TestBackfill:
    def test_backfill_chronological(self, pipeline, store, provider):
        provider.generate.return_value = json.dumps(
            [
                {"text": "User prefers Python", "category": "preference", "confidence": 0.8},
            ]
        )
        entries = [
            {
                "path": "e2",
                "content": "Second entry " * 10,
                "created": "2025-01-02",
                "type": "daily",
                "tags": [],
            },
            {
                "path": "e1",
                "content": "First entry " * 10,
                "created": "2025-01-01",
                "type": "daily",
                "tags": [],
            },
        ]
        stats = pipeline.backfill(entries)
        assert stats["entries_processed"] == 2
        assert stats["facts_extracted"] == 2

    def test_backfill_skips_short(self, pipeline, store, provider):
        entries = [
            {
                "path": "e1",
                "content": "short",
                "created": "2025-01-01",
                "type": "daily",
                "tags": [],
            },
        ]
        stats = pipeline.backfill(entries)
        assert stats["entries_processed"] == 0


class TestReextract:
    def test_reextract_deletes_old_first(self, pipeline, store, provider):
        # First extraction
        provider.generate.return_value = json.dumps(
            [
                {"text": "User likes Java", "category": "preference", "confidence": 0.8},
            ]
        )
        pipeline.process_journal_entry("entry-1", "I like Java for enterprise development work.")

        # Re-extract with different result
        provider.generate.return_value = json.dumps(
            [
                {"text": "User likes Kotlin", "category": "preference", "confidence": 0.85},
            ]
        )
        pipeline.reextract_entry("entry-1", "Actually I prefer Kotlin over Java for new projects.")

        active = store.get_all_active()
        texts = [f.text for f in active]
        assert "User likes Kotlin" in texts
        # Old fact should be soft-deleted
        assert "User likes Java" not in texts
