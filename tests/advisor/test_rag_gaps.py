"""Tests for RAG retriever coverage gaps — memory, recurring thoughts, build_context flags."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from advisor.rag import RAGRetriever
from memory.models import FactCategory, StewardFact


def _make_rag(fact_store=None, thread_store=None, memory_config=None):
    from journal.search import JournalSearch

    journal_search = MagicMock(spec=JournalSearch)
    journal_search.get_context_for_query.return_value = "journal text"
    journal_search.storage = MagicMock()

    return RAGRetriever(
        journal_search=journal_search,
        fact_store=fact_store,
        thread_store=thread_store,
        memory_config=memory_config or {},
    )


def _make_fact(id, text, category, confidence=0.8):
    return StewardFact(
        id=id,
        text=text,
        category=category,
        source_type="journal",
        source_id="j1",
        confidence=confidence,
    )


# ── get_memory_context ──


class TestGetMemoryContext:
    def test_no_fact_store_empty(self):
        rag = _make_rag(fact_store=None)
        assert rag.get_memory_context("test") == ""

    def test_fact_store_with_facts_returns_block(self):
        fs = MagicMock()
        fact = _make_fact("f1", "Prefers Python", FactCategory.PREFERENCE, confidence=0.95)
        fs.search.return_value = [fact]
        fs.get_all_active.return_value = [fact]

        rag = _make_rag(fact_store=fs, memory_config={"high_confidence_threshold": 0.9})
        result = rag.get_memory_context("coding")
        assert "<user_memory>" in result
        assert "Prefers Python" in result
        assert "</user_memory>" in result

    def test_exception_returns_empty(self):
        fs = MagicMock()
        fs.search.side_effect = RuntimeError("db gone")
        fs.get_all_active.side_effect = RuntimeError("db gone")

        rag = _make_rag(fact_store=fs)
        assert rag.get_memory_context("test") == ""

    def test_no_facts_returns_empty(self):
        fs = MagicMock()
        fs.search.return_value = []
        fs.get_all_active.return_value = []

        rag = _make_rag(fact_store=fs)
        assert rag.get_memory_context("test") == ""


# ── _format_memory_block ──


class TestFormatMemoryBlock:
    def test_facts_grouped_by_category(self):
        rag = _make_rag()
        facts = [
            _make_fact("f1", "Likes TDD", FactCategory.PREFERENCE, 0.9),
            _make_fact("f2", "Python expert", FactCategory.SKILL, 0.8),
            _make_fact("f3", "Prefers CLI", FactCategory.PREFERENCE, 0.7),
        ]
        result = rag._format_memory_block(facts)
        assert "## Preferences" in result
        assert "## Skills" in result
        # Within Preferences, higher confidence first
        pref_idx_tdd = result.index("Likes TDD")
        pref_idx_cli = result.index("Prefers CLI")
        assert pref_idx_tdd < pref_idx_cli

    def test_display_order_respected(self):
        rag = _make_rag()
        facts = [
            _make_fact("f1", "Working on X", FactCategory.CONTEXT, 0.9),
            _make_fact("f2", "Constrained time", FactCategory.CONSTRAINT, 0.8),
            _make_fact("f3", "Prefers vim", FactCategory.PREFERENCE, 0.9),
        ]
        result = rag._format_memory_block(facts)
        ctx_idx = result.index("Current Context")
        pref_idx = result.index("Preferences")
        const_idx = result.index("Constraints")
        assert ctx_idx < pref_idx < const_idx

    def test_sorted_by_confidence_within_group(self):
        rag = _make_rag()
        facts = [
            _make_fact("f1", "Low conf skill", FactCategory.SKILL, 0.5),
            _make_fact("f2", "High conf skill", FactCategory.SKILL, 0.95),
        ]
        result = rag._format_memory_block(facts)
        high_idx = result.index("High conf skill")
        low_idx = result.index("Low conf skill")
        assert high_idx < low_idx


# ── get_recurring_thoughts_context ──


class TestGetRecurringThoughtsContext:
    def test_no_thread_store_empty(self):
        rag = _make_rag(thread_store=None)
        assert rag.get_recurring_thoughts_context() == ""

    def test_exception_returns_empty(self):
        ts = MagicMock()
        ts.get_active_threads.side_effect = RuntimeError("db gone")
        rag = _make_rag(thread_store=ts)
        # The method catches all exceptions and returns ""
        assert rag.get_recurring_thoughts_context() == ""

    def test_thread_store_with_active_threads(self):
        now = datetime.now()

        @dataclass
        class FakeThread:
            id: str = "t1"
            label: str = "career switch"
            entry_count: int = 5
            created_at: datetime = now - timedelta(days=30)
            updated_at: datetime = now
            strength: float = 0.8

        @dataclass
        class FakeEntry:
            entry_date: datetime = now - timedelta(days=1)

        ts = MagicMock()
        fake_thread = FakeThread()
        fake_entries = [FakeEntry(), FakeEntry(), FakeEntry()]

        rag = _make_rag(thread_store=ts)

        with patch.object(rag, "_run_async") as mock_run_async:
            mock_run_async.side_effect = [
                [fake_thread],
                fake_entries,
            ]
            result = rag.get_recurring_thoughts_context()

        assert "<recurring_thoughts>" in result
        assert "career switch" in result
        assert "</recurring_thoughts>" in result

    def test_no_recent_entries_returns_empty(self):
        now = datetime.now()

        @dataclass
        class FakeThread:
            id: str = "t1"
            label: str = "old topic"
            entry_count: int = 2
            created_at: datetime = now - timedelta(days=90)
            updated_at: datetime = now - timedelta(days=60)
            strength: float = 0.01

        @dataclass
        class FakeEntry:
            entry_date: datetime = now - timedelta(days=60)

        ts = MagicMock()
        rag = _make_rag(thread_store=ts)

        with patch.object(rag, "_run_async") as mock_run_async:
            mock_run_async.side_effect = [
                [FakeThread()],
                [FakeEntry()],
            ]
            result = rag.get_recurring_thoughts_context()

        assert result == ""

    def test_threads_rank_by_strength_over_recent_count(self):
        now = datetime.now()

        @dataclass
        class FakeThread:
            id: str
            label: str
            entry_count: int
            created_at: datetime
            updated_at: datetime
            strength: float

        @dataclass
        class FakeEntry:
            entry_date: datetime

        strong = FakeThread(
            id="strong",
            label="deep focus",
            entry_count=3,
            created_at=now - timedelta(days=21),
            updated_at=now - timedelta(days=1),
            strength=0.9,
        )
        noisy = FakeThread(
            id="noisy",
            label="busywork",
            entry_count=6,
            created_at=now - timedelta(days=21),
            updated_at=now - timedelta(days=1),
            strength=0.3,
        )

        ts = MagicMock()
        rag = _make_rag(thread_store=ts)

        import asyncio

        with patch.object(asyncio, "get_running_loop", side_effect=RuntimeError):
            with patch.object(asyncio, "run") as mock_run:
                mock_run.side_effect = [
                    [noisy, strong],
                    [FakeEntry(now - timedelta(days=1)) for _ in range(5)],
                    [FakeEntry(now - timedelta(days=2)) for _ in range(2)],
                ]
                result = rag.get_recurring_thoughts_context()

        lines = result.splitlines()
        assert any("deep focus" in line for line in lines)
        ranked_lines = [line for line in lines if line[:2] in {"1.", "2."}]
        assert "deep focus" in ranked_lines[0]


# ── build_context_for_ask flags ──


class TestBuildContextForAskFlags:
    def test_inject_memory_true(self):
        rag = _make_rag()
        rag.get_memory_context = MagicMock(return_value="<user_memory>facts</user_memory>")
        ctx = rag.build_context_for_ask("q", {"inject_memory": True})
        assert "<user_memory>" in ctx.memory
        rag.get_memory_context.assert_called_once_with("q")

    def test_inject_recurring_thoughts_true(self):
        rag = _make_rag()
        rag.get_recurring_thoughts_context = MagicMock(
            return_value="<recurring_thoughts>stuff</recurring_thoughts>"
        )
        ctx = rag.build_context_for_ask("q", {"inject_recurring_thoughts": True})
        assert "<recurring_thoughts>" in ctx.thoughts
        rag.get_recurring_thoughts_context.assert_called_once()

    def test_both_false_empty_and_not_called(self):
        rag = _make_rag()
        rag.get_memory_context = MagicMock()
        rag.get_recurring_thoughts_context = MagicMock()
        ctx = rag.build_context_for_ask(
            "q", {"inject_memory": False, "inject_recurring_thoughts": False}
        )
        assert ctx.memory == ""
        assert ctx.thoughts == ""
        rag.get_memory_context.assert_not_called()
        rag.get_recurring_thoughts_context.assert_not_called()

    def test_structured_profile_true(self):
        rag = _make_rag()
        rag.get_profile_context = MagicMock(return_value="[IDENTITY]\nDev")
        ctx = rag.build_context_for_ask("q", {"structured_profile": True})
        assert "[IDENTITY]" in ctx.profile
        rag.get_profile_context.assert_called_once_with(structured=True)
