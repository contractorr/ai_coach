"""Tests for LLM factory and auto-detection."""

from unittest.mock import MagicMock, patch

import pytest

from llm import LLMError, create_llm_provider
from llm.factory import _auto_detect_provider, create_cheap_provider


class TestAutoDetection:
    def test_detects_anthropic_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        assert _auto_detect_provider() == "claude"

    def test_detects_openai_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        assert _auto_detect_provider() == "openai"

    def test_detects_google_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY", "AIza-test")
        assert _auto_detect_provider() == "gemini"

    def test_prefers_anthropic_when_multiple(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        assert _auto_detect_provider() == "claude"

    def test_no_keys_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        with pytest.raises(LLMError, match="No LLM API key found"):
            _auto_detect_provider()

    def test_explicit_unknown_key_does_not_fall_back_to_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-test")
        with pytest.raises(LLMError, match="Could not infer provider from explicit API key"):
            _auto_detect_provider(api_key="custom-key-format")


class TestCreateProvider:
    def test_explicit_claude_with_client(self):
        mock_client = MagicMock()
        provider = create_llm_provider(provider="claude", client=mock_client)
        assert provider.provider_name == "claude"
        assert provider.client is mock_client

    def test_explicit_openai_with_client(self):
        mock_client = MagicMock()
        provider = create_llm_provider(provider="openai", client=mock_client)
        assert provider.provider_name == "openai"
        assert provider.client is mock_client

    def test_explicit_gemini_with_client(self):
        mock_client = MagicMock()
        provider = create_llm_provider(provider="gemini", client=mock_client)
        assert provider.provider_name == "gemini"
        assert provider.client is mock_client

    def test_unknown_provider_raises(self):
        with pytest.raises(LLMError, match="Unknown provider"):
            create_llm_provider(provider="llama", client=MagicMock())

    def test_auto_with_anthropic_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        # Mock Anthropic client to avoid real init
        with patch("anthropic.Anthropic"):
            provider = create_llm_provider()
            assert provider.provider_name == "claude"

    def test_custom_model(self):
        mock_client = MagicMock()
        provider = create_llm_provider(
            provider="claude", client=mock_client, model="claude-opus-4-20250514"
        )
        assert provider.model == "claude-opus-4-20250514"

    def test_auto_with_explicit_unknown_key_raises(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-test")
        with pytest.raises(LLMError, match="Could not infer provider from explicit API key"):
            create_llm_provider(api_key="custom-key-format")

    def test_create_cheap_provider_with_explicit_unknown_key_raises(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-test")
        with pytest.raises(LLMError, match="Could not infer provider from explicit API key"):
            create_cheap_provider(api_key="custom-key-format")

    def test_default_models(self):
        mock_client = MagicMock()
        assert (
            create_llm_provider(provider="claude", client=mock_client).model == "claude-sonnet-4-6"
        )
        assert create_llm_provider(provider="openai", client=mock_client).model == "gpt-4o"
        assert (
            create_llm_provider(provider="gemini", client=mock_client).model_name
            == "gemini-2.5-flash"
        )
