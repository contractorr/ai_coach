"""Tests for OpenAI-compatible provider."""

import pytest

from llm.base import LLMError
from llm.providers.openai_compatible import OpenAICompatibleProvider


def test_requires_base_url():
    """OpenAICompatibleProvider requires base_url."""
    with pytest.raises(LLMError, match="base_url required"):
        OpenAICompatibleProvider(base_url="", api_key="test", model="test")


def test_requires_api_key():
    """OpenAICompatibleProvider requires api_key."""
    with pytest.raises(LLMError, match="api_key required"):
        OpenAICompatibleProvider(base_url="https://api.test.com", api_key="", model="test")


def test_requires_model():
    """OpenAICompatibleProvider requires model."""
    with pytest.raises(LLMError, match="model required"):
        OpenAICompatibleProvider(base_url="https://api.test.com", api_key="test", model="")


def test_display_name_defaults_to_generic():
    """Display name defaults to 'OpenAI-compatible' when not provided."""

    class _FakeOpenAI:
        def __init__(self, api_key, base_url):
            self.api_key = api_key
            self.base_url = base_url

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    pass

    # Monkey patch OpenAI import
    import sys

    class _MockModule:
        OpenAI = _FakeOpenAI

    sys.modules["openai"] = _MockModule()

    try:
        provider = OpenAICompatibleProvider(
            base_url="https://api.test.com", api_key="test-key", model="test-model"
        )
        assert provider.display_name == "OpenAI-compatible"
        assert provider.base_url == "https://api.test.com"
        assert provider.model == "test-model"
    finally:
        if "openai" in sys.modules:
            del sys.modules["openai"]


def test_display_name_can_be_customized():
    """Display name can be set to custom value."""

    class _FakeOpenAI:
        def __init__(self, api_key, base_url):
            self.api_key = api_key
            self.base_url = base_url

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    pass

    import sys

    class _MockModule:
        OpenAI = _FakeOpenAI

    sys.modules["openai"] = _MockModule()

    try:
        provider = OpenAICompatibleProvider(
            base_url="https://api.together.xyz/v1",
            api_key="test-key",
            model="llama-3-70b",
            display_name="Together Llama 3",
        )
        assert provider.display_name == "Together Llama 3"
    finally:
        if "openai" in sys.modules:
            del sys.modules["openai"]
