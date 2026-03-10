"""Tests for LLM provider adapters."""

from unittest.mock import MagicMock

import pytest

from llm import LLMAuthError, LLMError, LLMRateLimitError
from llm.base import LLMProvider
from llm.providers.claude import ClaudeProvider
from llm.providers.gemini import GeminiProvider
from llm.providers.openai import OpenAIProvider


class TestStripThinkTags:
    def test_strips_think_block(self):
        assert LLMProvider._strip_think_tags("<think>reasoning</think>Answer") == "Answer"

    def test_strips_multiline(self):
        text = "<think>\nstep 1\nstep 2\n</think>\nFinal answer"
        assert LLMProvider._strip_think_tags(text) == "Final answer"

    def test_strips_multiple_blocks(self):
        text = "<think>a</think>Hello <think>b</think>world"
        assert LLMProvider._strip_think_tags(text) == "Hello world"

    def test_case_insensitive(self):
        assert LLMProvider._strip_think_tags("<THINK>x</THINK>OK") == "OK"
        assert LLMProvider._strip_think_tags("<Think>x</Think>OK") == "OK"

    def test_none_passthrough(self):
        assert LLMProvider._strip_think_tags(None) is None

    def test_empty_string_passthrough(self):
        assert LLMProvider._strip_think_tags("") == ""

    def test_no_tags_unchanged(self):
        assert LLMProvider._strip_think_tags("just normal text") == "just normal text"

    def test_preserves_word_think(self):
        text = "I think this is correct"
        assert LLMProvider._strip_think_tags(text) == text

    def test_all_think_falls_back(self):
        # If stripping removes everything, return original
        assert (
            LLMProvider._strip_think_tags("<think>only this</think>") == "<think>only this</think>"
        )


class TestClaudeProvider:
    def test_generate(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="Hello from Claude")]
        mock_client.messages.create.return_value = mock_resp

        provider = ClaudeProvider(client=mock_client)
        result = provider.generate(
            messages=[{"role": "user", "content": "hi"}],
            system="Be helpful",
            max_tokens=100,
        )

        assert result == "Hello from Claude"

    def test_generate_strips_think_tags(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="<think>internal</think>Clean answer")]
        mock_client.messages.create.return_value = mock_resp

        provider = ClaudeProvider(client=mock_client)
        result = provider.generate(messages=[{"role": "user", "content": "hi"}])
        assert result == "Clean answer"

    def test_generate_no_system(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="response")]
        mock_client.messages.create.return_value = mock_resp

        provider = ClaudeProvider(client=mock_client)
        provider.generate(messages=[{"role": "user", "content": "hi"}])

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "system" not in call_kwargs

    def test_auth_error(self):
        from anthropic import AuthenticationError

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = AuthenticationError(
            message="bad key", response=MagicMock(status_code=401), body={}
        )

        provider = ClaudeProvider(client=mock_client)
        with pytest.raises(LLMAuthError):
            provider.generate(messages=[{"role": "user", "content": "hi"}])

    def test_rate_limit_error(self):
        from anthropic import RateLimitError

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RateLimitError(
            message="rate limited", response=MagicMock(status_code=429), body={}
        )

        provider = ClaudeProvider(client=mock_client)
        with pytest.raises(LLMRateLimitError):
            provider.generate(messages=[{"role": "user", "content": "hi"}])

    def test_api_error(self):
        from anthropic import APIError

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = APIError(
            message="server error", request=MagicMock(), body=None
        )

        provider = ClaudeProvider(client=mock_client)
        with pytest.raises(LLMError):
            provider.generate(messages=[{"role": "user", "content": "hi"}])


class TestOpenAIProvider:
    def test_generate(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="Hello from GPT"))]
        mock_client.chat.completions.create.return_value = mock_resp

        provider = OpenAIProvider(client=mock_client)
        result = provider.generate(
            messages=[{"role": "user", "content": "hi"}],
            system="Be helpful",
        )

        assert result == "Hello from GPT"

    def test_generate_strips_think_tags(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="<think>cot</think>Result"))]
        mock_client.chat.completions.create.return_value = mock_resp

        provider = OpenAIProvider(client=mock_client)
        result = provider.generate(messages=[{"role": "user", "content": "hi"}])
        assert result == "Result"

    def test_generate_no_system(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="response"))]
        mock_client.chat.completions.create.return_value = mock_resp

        provider = OpenAIProvider(client=mock_client)
        provider.generate(messages=[{"role": "user", "content": "hi"}])

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert len(call_kwargs["messages"]) == 1  # No system prepended


class TestGeminiProvider:
    def test_generate(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "Hello from Gemini"
        mock_client.models.generate_content.return_value = mock_resp

        provider = GeminiProvider(client=mock_client)
        result = provider.generate(
            messages=[{"role": "user", "content": "hi"}],
            system="Be helpful",
        )

        assert result == "Hello from Gemini"

    def test_generate_strips_think_tags(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "<think>step1\nstep2</think>Gemini answer"
        mock_client.models.generate_content.return_value = mock_resp

        provider = GeminiProvider(client=mock_client)
        result = provider.generate(messages=[{"role": "user", "content": "hi"}])
        assert result == "Gemini answer"

    def test_generate_no_system(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "response"
        mock_client.models.generate_content.return_value = mock_resp

        provider = GeminiProvider(client=mock_client)
        provider.generate(messages=[{"role": "user", "content": "hi"}])

        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert "System:" not in call_kwargs["contents"]

    def test_auth_error(self):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API key not valid")

        provider = GeminiProvider(client=mock_client)
        with pytest.raises(LLMAuthError):
            provider.generate(messages=[{"role": "user", "content": "hi"}])

    def test_generic_error(self):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("something broke")

        provider = GeminiProvider(client=mock_client)
        with pytest.raises(LLMError):
            provider.generate(messages=[{"role": "user", "content": "hi"}])
