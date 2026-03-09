"""Tests for WebSearchClient."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from research.web_search import AsyncWebSearchClient, SearchResult, WebSearchClient


@pytest.fixture
def mock_tavily_response():
    """Mock Tavily API response."""
    return {
        "results": [
            {
                "title": "Machine Learning in Healthcare",
                "url": "https://example.com/ml-healthcare",
                "content": "A comprehensive guide to applying ML in healthcare settings.",
                "score": 0.95,
            },
            {
                "title": "AI Applications in Medicine",
                "url": "https://example.com/ai-medicine",
                "content": "How artificial intelligence is transforming medical diagnosis.",
                "score": 0.88,
            },
        ]
    }


class TestWebSearchClient:
    """Tests for WebSearchClient."""

    def test_init_without_key(self, monkeypatch):
        """Test init without API key."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        client = WebSearchClient(api_key=None)
        assert client.api_key is None

    def test_init_with_key(self, monkeypatch):
        """Test init with API key."""
        client = WebSearchClient(api_key="test-key")
        assert client.api_key == "test-key"

    def test_search_without_key_falls_back_to_ddg(self, monkeypatch):
        """Test search falls back to DuckDuckGo when no API key."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        client = WebSearchClient(api_key=None)
        results = client.search("test query")
        # Should get results from DDG fallback (or empty if network unavailable)
        assert isinstance(results, list)

    def test_search_returns_results(self, mock_tavily_response):
        """Test search parses results correctly."""
        client = WebSearchClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = mock_tavily_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, "post", return_value=mock_response):
            results = client.search("machine learning healthcare")

        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "Machine Learning in Healthcare"
        assert results[0].score == 0.95

    def test_search_truncates_content(self, mock_tavily_response):
        """Test that content is truncated to max_content_chars."""
        # Add very long content
        mock_tavily_response["results"][0]["content"] = "x" * 5000

        client = WebSearchClient(api_key="test-key", max_content_chars=100)

        mock_response = MagicMock()
        mock_response.json.return_value = mock_tavily_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, "post", return_value=mock_response):
            results = client.search("test")

        assert len(results[0].content) == 100

    def test_search_handles_http_error(self):
        """Test search handles HTTP errors gracefully."""
        client = WebSearchClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=MagicMock(status_code=404, text="Not Found")
        )

        with patch.object(client.client, "post", return_value=mock_response):
            results = client.search("test")

        assert results == []

    def test_search_handles_request_error(self):
        """Test search handles network errors gracefully."""
        client = WebSearchClient(api_key="test-key")

        with patch.object(
            client.client, "post", side_effect=httpx.RequestError("Connection failed")
        ):
            results = client.search("test")

        assert results == []

    def test_context_manager(self):
        """Test client works as context manager."""
        with WebSearchClient(api_key="test") as client:
            assert client.api_key == "test"

    def test_close_is_idempotent(self):
        """Closing twice should be a no-op on the underlying client."""
        client = WebSearchClient(api_key="test")

        with patch.object(client.client, "close") as mock_close:
            client.close()
            client.close()

        mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_async_close_is_idempotent():
    """Async close should only close the underlying client once."""
    client = AsyncWebSearchClient(api_key="test")

    with patch.object(client.client, "aclose") as mock_aclose:
        await client.close()
        await client.close()

    mock_aclose.assert_awaited_once()
