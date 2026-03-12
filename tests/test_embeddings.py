"""Tests for configurable embedding provider factory."""

from unittest.mock import patch


class TestEmbeddingFactory:
    """Test create_embedding_function auto-detection and config."""

    def test_hash_fallback_no_keys(self, monkeypatch):
        """No API keys → hash fallback."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from embeddings.factory import create_embedding_function

        fn = create_embedding_function()
        assert fn.name() == "simple-hash-fallback"

    def test_explicit_hash_provider(self, monkeypatch):
        """provider='hash' always returns hash regardless of env."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

        from embeddings.factory import create_embedding_function

        fn = create_embedding_function(provider="hash")
        assert fn.name() == "simple-hash-fallback"

    def test_hash_custom_dimensions(self):
        """Hash fallback respects custom dimensions."""
        from embeddings.factory import create_embedding_function

        fn = create_embedding_function(provider="hash", dimensions=512)
        assert fn.dimensions == 512

    def test_auto_detects_gemini(self, monkeypatch):
        """GOOGLE_API_KEY present → selects gemini."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with patch("google.genai.Client"):
            from embeddings.factory import create_embedding_function

            fn = create_embedding_function(provider="gemini")
            assert fn.provider_name == "gemini"
            assert fn.dimensions == 768

    def test_auto_detects_openai(self, monkeypatch):
        """OPENAI_API_KEY present (no Google key) → selects openai."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        with patch("openai.OpenAI"):
            from embeddings.factory import create_embedding_function

            fn = create_embedding_function(provider="openai")
            assert fn.provider_name == "openai"
            assert fn.dimensions == 1536

    def test_config_dict_respected(self, monkeypatch):
        """Config dict values used when provided."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from embeddings.factory import create_embedding_function

        config = {"embeddings": {"provider": "hash", "dimensions": 128}}
        fn = create_embedding_function(config=config)
        assert fn.name() == "simple-hash-fallback"
        assert fn.dimensions == 128

    def test_gemini_priority_over_openai(self, monkeypatch):
        """Both keys present → gemini wins."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        from embeddings.factory import _auto_detect_provider

        assert _auto_detect_provider() == "gemini"

    def test_unknown_provider_falls_back(self, monkeypatch):
        """Unknown provider name → hash fallback."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from embeddings.factory import create_embedding_function

        fn = create_embedding_function(provider="nonexistent")
        assert fn.name() == "simple-hash-fallback"


class TestHashEmbeddingFunction:
    """Test SimpleHashEmbeddingFunction behavior."""

    def test_deterministic(self):
        """Same input → same output."""
        from chroma_utils import SimpleHashEmbeddingFunction

        fn = SimpleHashEmbeddingFunction()
        result1 = fn(["hello world"])
        result2 = fn(["hello world"])
        assert result1 == result2

    def test_normalized(self):
        """Output vectors are L2-normalized."""
        import math

        from chroma_utils import SimpleHashEmbeddingFunction

        fn = SimpleHashEmbeddingFunction()
        [vec] = fn(["some text for embedding"])
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-6

    def test_empty_input(self):
        """Empty string → zero vector."""
        from chroma_utils import SimpleHashEmbeddingFunction

        fn = SimpleHashEmbeddingFunction()
        [vec] = fn([""])
        assert all(v == 0.0 for v in vec)

    def test_correct_dimensions(self):
        """Output matches configured dimensions."""
        from chroma_utils import SimpleHashEmbeddingFunction

        fn = SimpleHashEmbeddingFunction(dimensions=512)
        [vec] = fn(["test"])
        assert len(vec) == 512

    def test_batch_input(self):
        """Multiple inputs return multiple vectors."""
        from chroma_utils import SimpleHashEmbeddingFunction

        fn = SimpleHashEmbeddingFunction()
        result = fn(["hello", "world", "test"])
        assert len(result) == 3
        assert all(len(v) == 256 for v in result)


class TestBuildEmbeddingFunction:
    """Test chroma_utils.build_embedding_function delegation."""

    def test_delegates_to_factory(self, monkeypatch):
        """build_embedding_function uses the new factory."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from chroma_utils import build_embedding_function

        fn = build_embedding_function()
        # With no API keys, should get hash fallback
        assert fn is not None
        result = fn(["test"])
        assert len(result) == 1
        assert len(result[0]) == 256
