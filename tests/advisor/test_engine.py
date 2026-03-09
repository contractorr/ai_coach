"""Tests for AdvisorEngine."""

from unittest.mock import MagicMock

import pytest

from advisor.engine import AdvisorEngine, APIKeyMissingError, LLMError
from advisor.council import CouncilMember


@pytest.fixture
def mock_rag():
    rag = MagicMock()
    rag.get_combined_context.return_value = ("journal ctx", "intel ctx")
    rag.get_recent_entries.return_value = "recent entries"
    rag.get_intel_context.return_value = "intel context"
    rag.get_filtered_intel_context.return_value = "intel context"
    rag.get_journal_context.return_value = "journal context"
    rag.get_research_context.return_value = ""
    rag.get_profile_keywords.return_value = []
    return rag


@pytest.fixture
def mock_client():
    """Mock Claude SDK client (passed through to ClaudeProvider)."""
    client = MagicMock()
    resp = MagicMock()
    resp.content = [MagicMock(text="Mocked LLM response")]
    client.messages.create.return_value = resp
    return client


@pytest.fixture
def engine(mock_rag, mock_client):
    return AdvisorEngine(rag=mock_rag, provider="claude", client=mock_client)


class TestAdvisorEngine:
    def test_init_requires_api_key(self, mock_rag, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        with pytest.raises(APIKeyMissingError):
            AdvisorEngine(rag=mock_rag)

    def test_init_with_client(self, mock_rag, mock_client):
        engine = AdvisorEngine(rag=mock_rag, provider="claude", client=mock_client)
        assert engine.llm.client is mock_client

    def test_ask_general(self, engine, mock_client):
        result = engine.ask("What should I learn?")
        assert result == "Mocked LLM response"
        mock_client.messages.create.assert_called_once()

    def test_ask_career(self, engine, mock_client):
        result = engine.ask("Career advice?", advice_type="career")
        assert isinstance(result, str)
        assert mock_client.messages.create.called

    def test_ask_includes_research_context(self, engine, mock_rag):
        mock_rag.get_research_context.return_value = "research data here"
        engine.ask("test", include_research=True)
        mock_rag.get_research_context.assert_called()

    def test_ask_skips_research_when_disabled(self, engine, mock_rag):
        engine.ask("test", include_research=False)
        mock_rag.get_research_context.assert_not_called()

    def test_weekly_review(self, engine, mock_client):
        result = engine.weekly_review()
        assert isinstance(result, str)
        assert mock_client.messages.create.called

    def test_weekly_review_with_stale_goals(self, engine, mock_client, populated_journal):
        result = engine.weekly_review(journal_storage=populated_journal["storage"])
        assert isinstance(result, str)

    def test_detect_opportunities(self, engine, mock_client):
        result = engine.detect_opportunities()
        assert isinstance(result, str)
        assert mock_client.messages.create.called

    def test_analyze_goals(self, engine, mock_client):
        result = engine.analyze_goals()
        assert isinstance(result, str)

    def test_analyze_goals_specific(self, engine, mock_client):
        result = engine.analyze_goals(specific_goal="Learn Rust")
        assert isinstance(result, str)

    def test_llm_auth_error(self, mock_rag):
        from anthropic import AuthenticationError

        client = MagicMock()
        client.messages.create.side_effect = AuthenticationError(
            message="bad key", response=MagicMock(status_code=401), body={}
        )
        engine = AdvisorEngine(rag=mock_rag, provider="claude", client=client)
        with pytest.raises(LLMError):
            engine.ask("test")

    def test_generate_recommendations(self, engine, tmp_path):
        db_path = tmp_path / "recs.db"
        recs = engine.generate_recommendations("learning", db_path)
        assert isinstance(recs, list)

    def test_generate_action_brief(self, engine, tmp_path):
        db_path = tmp_path / "recs.db"
        brief = engine.generate_action_brief(db_path)
        assert isinstance(brief, str)

    def test_provider_name_accessible(self, engine):
        assert engine.llm.provider_name == "claude"

    def test_council_used_for_important_decision_prompt(self, mock_rag, mock_client):
        calls = []

        class FakeCouncilProvider:
            def __init__(self, provider_name):
                self.provider_name = provider_name

            def generate(self, messages, system=None, max_tokens=2000, use_thinking=False):
                calls.append((self.provider_name, messages[-1]["content"]))
                if "COUNCIL RESPONSES:" in messages[-1]["content"]:
                    return "Synthesized council answer"
                return f"Independent answer from {self.provider_name}"

        engine = AdvisorEngine(
            rag=mock_rag,
            provider="claude",
            client=mock_client,
            council_members=[
                CouncilMember(provider="claude", api_key="k1"),
                CouncilMember(provider="openai", api_key="k2"),
            ],
            council_lead_provider="claude",
            council_provider_factory=lambda provider, **kwargs: FakeCouncilProvider(provider),
        )

        result = engine.ask_result("Help me decide between two offers with different tradeoffs")

        assert result.council_used is True
        assert result.answer == "Synthesized council answer"
        assert set(result.council_providers) == {"claude", "openai"}
        mock_client.messages.create.assert_not_called()
        assert len(calls) == 3

    def test_council_skips_low_risk_prompt(self, mock_rag, mock_client):
        engine = AdvisorEngine(
            rag=mock_rag,
            provider="claude",
            client=mock_client,
            council_members=[
                CouncilMember(provider="claude", api_key="k1"),
                CouncilMember(provider="openai", api_key="k2"),
            ],
        )

        result = engine.ask_result("What is Rust?")

        assert result.council_used is False
        assert result.answer == "Mocked LLM response"
        mock_client.messages.create.assert_called_once()


class TestContextAssemblyWiring:
    """Test rag_config wiring in ask()."""

    def _make_engine(self, mock_rag, mock_client, rag_config=None):
        return AdvisorEngine(
            rag=mock_rag, provider="claude", client=mock_client, rag_config=rag_config
        )

    def test_default_config_uses_legacy_path(self, mock_rag, mock_client):
        """No rag_config flags → legacy get_combined_context + get_profile_context."""
        engine = self._make_engine(mock_rag, mock_client)
        engine.ask("test")
        mock_rag.get_combined_context.assert_called_once()
        mock_rag.get_profile_context.assert_called_once()

    def test_inject_memory_calls_build_context(self, mock_rag, mock_client):
        """inject_memory=True → build_context_for_ask used."""
        from advisor.rag import AskContext

        mock_rag.build_context_for_ask.return_value = AskContext(
            journal="j", intel="i", profile="p", memory="<user_memory>\nfacts\n</user_memory>"
        )
        engine = self._make_engine(mock_rag, mock_client, rag_config={"inject_memory": True})
        result = engine.ask("test")

        mock_rag.build_context_for_ask.assert_called_once()
        assert result == "Mocked LLM response"
        # Verify memory appeared in the prompt sent to LLM
        call_args = mock_client.messages.create.call_args
        user_msg = [m for m in call_args.kwargs["messages"] if m["role"] == "user"][0]
        assert "<user_memory>" in user_msg["content"]

    def test_xml_delimiters_in_prompt(self, mock_rag, mock_client):
        """xml_delimiters=True → XML tags in prompt."""
        from advisor.rag import AskContext

        mock_rag.build_context_for_ask.return_value = AskContext(
            journal="j", intel="i", profile="p"
        )
        engine = self._make_engine(mock_rag, mock_client, rag_config={"xml_delimiters": True})
        engine.ask("test")

        call_args = mock_client.messages.create.call_args
        user_msg = [m for m in call_args.kwargs["messages"] if m["role"] == "user"][0]
        assert "<journal_context>" in user_msg["content"]
        assert "<user_profile>" in user_msg["content"]

    def test_no_memory_in_default_prompt(self, mock_rag, mock_client):
        """Default config → no memory XML in prompt."""
        engine = self._make_engine(mock_rag, mock_client)
        engine.ask("test")

        call_args = mock_client.messages.create.call_args
        user_msg = [m for m in call_args.kwargs["messages"] if m["role"] == "user"][0]
        assert "<user_memory>" not in user_msg["content"]

    def test_attachment_ids_force_document_context(self, mock_rag, mock_client):
        """Attachment IDs should trigger extended document-grounded prompt assembly."""
        from advisor.rag import AskContext

        mock_rag.build_context_for_ask.return_value = AskContext(
            journal="j",
            intel="i",
            profile="p",
            documents="DOCUMENT CONTEXT:\n[DOCUMENT] Resume\nPython leadership",
        )
        engine = self._make_engine(mock_rag, mock_client)

        engine.ask("Use my CV", attachment_ids=["doc-1"])

        mock_rag.build_context_for_ask.assert_called_once_with(
            "Use my CV", {}, attachment_ids=["doc-1"]
        )
        call_args = mock_client.messages.create.call_args
        user_msg = [m for m in call_args.kwargs["messages"] if m["role"] == "user"][0]
        assert "DOCUMENT CONTEXT" in user_msg["content"]
