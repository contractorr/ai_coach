"""Tests for trace accumulation in AgenticOrchestrator."""

from unittest.mock import MagicMock

import pytest

from advisor.agentic import AgenticOrchestrator
from advisor.tools import build_tool_registry
from llm.base import GenerateResponse, ToolCall


@pytest.fixture
def mock_components(tmp_path):
    from pathlib import Path

    from journal.storage import JournalStorage

    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()

    storage = JournalStorage(journal_dir)
    embeddings = MagicMock(name="embeddings")
    embeddings.query.return_value = []
    intel_storage = MagicMock(name="intel_storage")
    intel_storage.db_path = tmp_path / "intel.db"
    intel_storage.search.return_value = []
    intel_storage.get_recent.return_value = []
    rag = MagicMock(name="rag")
    rag.cache = None
    rag.intel_db_path = Path(tmp_path / "intel.db")

    return {
        "storage": storage,
        "embeddings": embeddings,
        "intel_storage": intel_storage,
        "rag": rag,
        "profile_path": str(tmp_path / "profile.yaml"),
        "recommendations_dir": tmp_path / "recommendations",
    }


@pytest.fixture
def registry(mock_components):
    return build_tool_registry(mock_components)


class TestTraceAccumulation:
    def test_immediate_answer_trace(self, registry):
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.return_value = GenerateResponse(
            content="Answer.", finish_reason="stop"
        )

        orch = AgenticOrchestrator(mock_llm, registry, "system", min_tool_calls=0)
        orch.run("hi")

        assert len(orch._trace) == 3  # session_start, llm_response, answer
        assert orch._trace[0]["type"] == "session_start"
        assert orch._trace[0]["session_id"] == orch._session_id
        assert orch._trace[1]["type"] == "llm_response"
        assert orch._trace[2]["type"] == "answer"

    def test_tool_call_trace(self, registry):
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.side_effect = [
            GenerateResponse(
                content=None,
                tool_calls=[ToolCall(id="t1", name="goals_list", arguments={})],
                finish_reason="tool_calls",
            ),
            GenerateResponse(content="Done.", finish_reason="stop"),
        ]

        orch = AgenticOrchestrator(mock_llm, registry, "system", min_tool_calls=0)
        orch.run("goals?")

        types = [e["type"] for e in orch._trace]
        assert types == [
            "session_start",
            "llm_response",
            "tool_start",
            "tool_done",
            "llm_response",
            "answer",
        ]
        # tool_start has correct tool name
        tool_start = [e for e in orch._trace if e["type"] == "tool_start"][0]
        assert tool_start["tool"] == "goals_list"
        assert tool_start["tool_call_id"] == "t1"

    def test_nudge_in_trace(self, registry):
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.side_effect = [
            GenerateResponse(content="Quick.", finish_reason="stop"),
            GenerateResponse(content="Final.", finish_reason="stop"),
        ]

        orch = AgenticOrchestrator(mock_llm, registry, "system", min_tool_calls=2)
        orch.run("question")

        types = [e["type"] for e in orch._trace]
        assert "nudge" in types
        nudge = [e for e in orch._trace if e["type"] == "nudge"][0]
        assert nudge["used_count"] == 0
        assert nudge["min_required"] == 2

    def test_max_iterations_trace(self, registry):
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.return_value = GenerateResponse(
            content=None,
            tool_calls=[ToolCall(id="t1", name="goals_list", arguments={})],
            finish_reason="tool_calls",
        )

        orch = AgenticOrchestrator(mock_llm, registry, "system", max_iterations=2)
        orch.run("loop")

        types = [e["type"] for e in orch._trace]
        assert types[-1] == "max_iterations_reached"
        assert orch._trace[-1]["max_iterations"] == 2

    def test_trace_resets_between_runs(self, registry):
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.return_value = GenerateResponse(
            content="ok", finish_reason="stop"
        )

        orch = AgenticOrchestrator(mock_llm, registry, "system", min_tool_calls=0)
        orch.run("first")
        first_id = orch._session_id
        first_len = len(orch._trace)

        orch.run("second")
        assert orch._session_id != first_id
        assert len(orch._trace) == first_len  # same structure, fresh list

    def test_all_entries_have_version_and_ts(self, registry):
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.side_effect = [
            GenerateResponse(
                content=None,
                tool_calls=[ToolCall(id="t1", name="goals_list", arguments={})],
                finish_reason="tool_calls",
            ),
            GenerateResponse(content="Done.", finish_reason="stop"),
        ]

        orch = AgenticOrchestrator(mock_llm, registry, "system", min_tool_calls=0)
        orch.run("q")

        for entry in orch._trace:
            assert "v" in entry
            assert entry["v"] == 1
            assert "ts" in entry
            assert isinstance(entry["ts"], float)
