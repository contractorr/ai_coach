"""Tests for AgenticOrchestrator and agentic engine integration."""

from types import SimpleNamespace
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
    embeddings.add_entry.return_value = None
    embeddings.sync_from_storage.return_value = None

    intel_db = tmp_path / "intel.db"
    intel_storage = MagicMock(name="intel_storage")
    intel_storage.db_path = intel_db
    intel_storage.search.return_value = []
    intel_storage.get_recent.return_value = []

    rag = MagicMock(name="rag")
    rag.cache = None
    rag.intel_db_path = Path(intel_db)
    rag.get_profile_context.return_value = ""
    rag.get_recent_entries.return_value = ""
    rag.get_journal_context.return_value = ""
    rag.get_research_context.return_value = ""
    rag.get_combined_context.return_value = ("", "")
    rag.build_context_for_ask.return_value = SimpleNamespace(
        journal="",
        intel="",
        profile="",
        memory="",
        thoughts="",
    )

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


class TestAgenticOrchestrator:
    def test_immediate_text_response(self, registry):
        """LLM returns text on first call — no tool use."""
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.return_value = GenerateResponse(
            content="Here's my advice.",
            finish_reason="stop",
        )

        orch = AgenticOrchestrator(mock_llm, registry, "system prompt")
        result = orch.run("What should I do?")

        assert result == "Here's my advice."
        assert mock_llm.generate_with_tools.call_count == 1

    def test_single_tool_call_then_text(self, registry):
        """LLM calls one tool, then responds with text."""
        mock_llm = MagicMock()

        # First call: tool use
        mock_llm.generate_with_tools.side_effect = [
            GenerateResponse(
                content=None,
                tool_calls=[ToolCall(id="t1", name="goals_list", arguments={})],
                finish_reason="tool_calls",
            ),
            # Second call: text response after getting tool result
            GenerateResponse(
                content="You have no goals yet.",
                finish_reason="stop",
            ),
        ]

        orch = AgenticOrchestrator(mock_llm, registry, "system prompt")
        result = orch.run("What are my goals?")

        assert result == "You have no goals yet."
        assert mock_llm.generate_with_tools.call_count == 2

        # Verify tool result was passed back in messages
        second_call_messages = mock_llm.generate_with_tools.call_args_list[1].kwargs["messages"]
        # user, assistant(tool_calls), tool(result)
        assert len(second_call_messages) == 3
        assert second_call_messages[0]["role"] == "user"
        assert second_call_messages[1]["role"] == "assistant"
        assert "tool_calls" in second_call_messages[1]
        assert second_call_messages[2]["role"] == "tool"

    def test_multiple_tool_calls_in_one_turn(self, registry):
        """LLM requests two tools in parallel."""
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.side_effect = [
            GenerateResponse(
                content=None,
                tool_calls=[
                    ToolCall(id="t1", name="goals_list", arguments={}),
                    ToolCall(id="t2", name="intel_get_recent", arguments={"days": 7}),
                ],
                finish_reason="tool_calls",
            ),
            GenerateResponse(content="Combined analysis.", finish_reason="stop"),
        ]

        orch = AgenticOrchestrator(mock_llm, registry, "system prompt")
        result = orch.run("How do my goals relate to recent news?")

        assert result == "Combined analysis."
        # Should have 4 messages: user, assistant, tool(t1), tool(t2)
        second_call_messages = mock_llm.generate_with_tools.call_args_list[1].kwargs["messages"]
        assert len(second_call_messages) == 4
        tool_msgs = [m for m in second_call_messages if m["role"] == "tool"]
        assert len(tool_msgs) == 2

    def test_multi_iteration_tool_calls(self, registry):
        """LLM calls tools across multiple iterations."""
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.side_effect = [
            # Iteration 1: list goals
            GenerateResponse(
                content=None,
                tool_calls=[ToolCall(id="t1", name="goals_list", arguments={})],
                finish_reason="tool_calls",
            ),
            # Iteration 2: search intel
            GenerateResponse(
                content=None,
                tool_calls=[ToolCall(id="t2", name="intel_search", arguments={"query": "rust"})],
                finish_reason="tool_calls",
            ),
            # Iteration 3: final response
            GenerateResponse(content="Final answer.", finish_reason="stop"),
        ]

        orch = AgenticOrchestrator(mock_llm, registry, "system prompt")
        result = orch.run("Analyze everything")

        assert result == "Final answer."
        assert mock_llm.generate_with_tools.call_count == 3

    def test_max_iterations_reached(self, registry):
        """Loop terminates at max_iterations."""
        mock_llm = MagicMock()
        # Always return tool calls, never stop
        mock_llm.generate_with_tools.return_value = GenerateResponse(
            content=None,
            tool_calls=[ToolCall(id="t1", name="goals_list", arguments={})],
            finish_reason="tool_calls",
        )

        orch = AgenticOrchestrator(mock_llm, registry, "system prompt", max_iterations=3)
        result = orch.run("infinite loop?")

        assert mock_llm.generate_with_tools.call_count == 3
        assert "wasn't able to complete" in result

    def test_max_iterations_with_partial_content(self, registry):
        """Returns partial content when max iterations hit and LLM produced text."""
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.return_value = GenerateResponse(
            content="Partial thought...",
            tool_calls=[ToolCall(id="t1", name="goals_list", arguments={})],
            finish_reason="tool_calls",
        )

        orch = AgenticOrchestrator(mock_llm, registry, "system prompt", max_iterations=2)
        result = orch.run("question")

        assert result == "Partial thought..."

    def test_tool_error_passed_back(self, registry):
        """Tool execution error is returned to LLM, not raised."""
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.side_effect = [
            GenerateResponse(
                content=None,
                tool_calls=[
                    ToolCall(id="t1", name="journal_read", arguments={"filename": "nonexistent.md"})
                ],
                finish_reason="tool_calls",
            ),
            GenerateResponse(content="That entry doesn't exist.", finish_reason="stop"),
        ]

        orch = AgenticOrchestrator(mock_llm, registry, "system prompt")
        result = orch.run("Read my entry")

        assert result == "That entry doesn't exist."
        # Verify error was in tool result message
        second_call_messages = mock_llm.generate_with_tools.call_args_list[1].kwargs["messages"]
        tool_msg = [m for m in second_call_messages if m["role"] == "tool"][0]
        assert tool_msg["is_error"] is True

    def test_unknown_tool_returns_error(self, registry):
        """Unknown tool name returns error to LLM."""
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.side_effect = [
            GenerateResponse(
                content=None,
                tool_calls=[ToolCall(id="t1", name="fake_tool", arguments={})],
                finish_reason="tool_calls",
            ),
            GenerateResponse(content="Sorry, that tool doesn't exist.", finish_reason="stop"),
        ]

        orch = AgenticOrchestrator(mock_llm, registry, "system prompt")
        result = orch.run("Do something weird")

        assert result == "Sorry, that tool doesn't exist."

    def test_system_prompt_passed(self, registry):
        """System prompt is forwarded to LLM."""
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.return_value = GenerateResponse(
            content="ok", finish_reason="stop"
        )

        orch = AgenticOrchestrator(mock_llm, registry, "You are a coach.")
        orch.run("hi")

        call_kwargs = mock_llm.generate_with_tools.call_args.kwargs
        assert call_kwargs["system"] == "You are a coach."

    def test_conversation_history_prepended(self, registry):
        """Conversation history appears before user message."""
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.return_value = GenerateResponse(
            content="Based on our earlier discussion...",
            finish_reason="stop",
        )

        history = [
            {"role": "user", "content": "What are my goals?"},
            {"role": "assistant", "content": "You have 3 goals."},
        ]

        orch = AgenticOrchestrator(mock_llm, registry, "system prompt")
        result = orch.run("Tell me more about goal 1", conversation_history=history)

        assert result == "Based on our earlier discussion..."
        call_messages = mock_llm.generate_with_tools.call_args.kwargs["messages"]
        assert len(call_messages) == 3
        assert call_messages[0] == history[0]
        assert call_messages[1] == history[1]
        assert call_messages[2]["content"] == "Tell me more about goal 1"

    def test_no_history_works(self, registry):
        """None history works same as before."""
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.return_value = GenerateResponse(
            content="ok",
            finish_reason="stop",
        )

        orch = AgenticOrchestrator(mock_llm, registry, "system")
        orch.run("hi", conversation_history=None)

        call_messages = mock_llm.generate_with_tools.call_args.kwargs["messages"]
        assert len(call_messages) == 1
        assert call_messages[0]["role"] == "user"

    def test_assistant_text_with_tool_calls_preserved(self, registry):
        """When LLM returns both text and tool_calls, text is in assistant msg."""
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.side_effect = [
            GenerateResponse(
                content="Let me check your goals.",
                tool_calls=[ToolCall(id="t1", name="goals_list", arguments={})],
                finish_reason="tool_calls",
            ),
            GenerateResponse(content="Here are your goals: none.", finish_reason="stop"),
        ]

        orch = AgenticOrchestrator(mock_llm, registry, "system")
        orch.run("goals?")

        second_call_messages = mock_llm.generate_with_tools.call_args_list[1].kwargs["messages"]
        assistant_msg = second_call_messages[1]
        assert assistant_msg["content"] == "Let me check your goals."
        assert "tool_calls" in assistant_msg

    def test_usage_is_tracked_on_response(self, registry):
        mock_llm = MagicMock()
        mock_llm.generate_with_tools.return_value = GenerateResponse(
            content="ok",
            finish_reason="stop",
            usage={"input_tokens": 321, "output_tokens": 12},
        )

        orch = AgenticOrchestrator(mock_llm, registry, "system")
        orch.run("hi")

        assert orch._total_input_tokens == 321


class TestAgenticEngineIntegration:
    def test_engine_with_use_tools(self, mock_components):
        """AdvisorEngine routes to orchestrator when use_tools=True."""
        from advisor.engine import AdvisorEngine

        mock_client = MagicMock()
        # generate_with_tools returns text immediately
        resp = MagicMock()
        resp.content = [MagicMock(type="text", text="Agentic response")]
        resp.stop_reason = "end_turn"
        mock_client.messages.create.return_value = resp

        engine = AdvisorEngine(
            rag=mock_components["rag"],
            provider="claude",
            client=mock_client,
            use_tools=True,
            components=mock_components,
        )

        assert engine._orchestrator is not None
        result = engine.ask("What are my goals?")
        assert isinstance(result, str)

    def test_engine_without_use_tools(self, mock_components):
        """AdvisorEngine uses classic RAG when use_tools=False."""
        from advisor.engine import AdvisorEngine

        mock_client = MagicMock()
        resp = MagicMock()
        resp.content = [MagicMock(text="RAG response")]
        mock_client.messages.create.return_value = resp

        engine = AdvisorEngine(
            rag=mock_components["rag"],
            provider="claude",
            client=mock_client,
            use_tools=False,
        )

        assert engine._orchestrator is None
        result = engine.ask("What should I learn?")
        assert result == "RAG response"

    def test_engine_use_tools_without_components_no_orchestrator(self, mock_components):
        """use_tools=True but no components dict → no orchestrator (falls back to RAG)."""
        from advisor.engine import AdvisorEngine

        mock_client = MagicMock()
        resp = MagicMock()
        resp.content = [MagicMock(text="RAG fallback")]
        mock_client.messages.create.return_value = resp

        engine = AdvisorEngine(
            rag=mock_components["rag"],
            provider="claude",
            client=mock_client,
            use_tools=True,
            components=None,
        )

        assert engine._orchestrator is None

    def test_dynamic_prompt_contains_goal_title(self, mock_components):
        """System prompt includes active goal titles when goals exist."""
        from advisor.engine import AdvisorEngine

        # Create a goal
        storage = mock_components["storage"]
        storage.create(content="Learn it", entry_type="goal", title="Master Rust")

        mock_client = MagicMock()
        resp = MagicMock()
        resp.content = [MagicMock(type="text", text="Coaching response")]
        resp.stop_reason = "end_turn"
        mock_client.messages.create.return_value = resp

        engine = AdvisorEngine(
            rag=mock_components["rag"],
            provider="claude",
            client=mock_client,
            use_tools=True,
            components=mock_components,
        )

        assert engine._orchestrator is not None
        assert "Master Rust" in engine._orchestrator.system_prompt
        assert "ACTIVE GOALS" in engine._orchestrator.system_prompt
