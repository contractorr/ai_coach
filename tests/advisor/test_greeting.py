"""Tests for greeting generation and cache helpers."""

from unittest.mock import MagicMock

import pytest

from advisor.context_cache import ContextCache
from advisor.greeting import (
    STATIC_FALLBACK,
    _build_greeting_prompt,
    cache_greeting,
    generate_greeting,
    get_cached_greeting,
    invalidate_greeting,
    make_greeting_cache_key,
)


class TestGreetingCacheKey:
    def test_format(self):
        assert make_greeting_cache_key("user-123") == "greeting_v1_user-123"

    def test_sanitizes_colons(self):
        assert make_greeting_cache_key("google:456") == "greeting_v1_google_456"


class TestBuildGreetingPrompt:
    def test_with_full_context(self):
        ctx = {
            "name": "Alice",
            "stale_goals": [{"title": "Learn Rust", "days_since_check": 7}],
            "recommendations": [{"title": "Try WebAssembly"}],
            "intel": [{"title": "Rust 1.80 released"}],
        }
        prompt = _build_greeting_prompt(ctx)
        assert "Alice" in prompt
        assert "Learn Rust" in prompt
        assert "Try WebAssembly" in prompt
        assert "Rust 1.80" in prompt

    def test_empty_context(self):
        prompt = _build_greeting_prompt({})
        assert "No context available" in prompt

    def test_partial_context(self):
        ctx = {"name": "Bob"}
        prompt = _build_greeting_prompt(ctx)
        assert "Bob" in prompt
        assert "Stale goals" not in prompt


class TestGenerateGreeting:
    def test_success(self):
        llm = MagicMock()
        llm.ask.return_value = "Great to see you back."
        ctx = {"name": "Test"}
        result = generate_greeting(ctx, llm)
        assert result == "Great to see you back."
        llm.ask.assert_called_once()

    def test_llm_returns_empty(self):
        llm = MagicMock()
        llm.ask.return_value = ""
        result = generate_greeting({}, llm)
        assert result == STATIC_FALLBACK

    def test_llm_raises(self):
        llm = MagicMock()
        llm.ask.side_effect = RuntimeError("API down")
        result = generate_greeting({}, llm)
        assert result == STATIC_FALLBACK


class TestGreetingCacheOps:
    @pytest.fixture
    def cache(self, tmp_path):
        return ContextCache(tmp_path / "cache.db", default_ttl=86400)

    def test_cache_roundtrip(self, cache):
        cache_greeting("user-1", cache, "Hello there")
        assert get_cached_greeting("user-1", cache) == "Hello there"

    def test_get_missing(self, cache):
        assert get_cached_greeting("user-999", cache) is None

    def test_invalidate(self, cache):
        cache_greeting("user-1", cache, "Hello")
        invalidate_greeting("user-1", cache)
        assert get_cached_greeting("user-1", cache) is None
