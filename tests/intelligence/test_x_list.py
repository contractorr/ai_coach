"""Tests for X/Twitter List scraper."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest


def _make_mock_client(response):
    """Create a mock httpx client with async get and aclose."""
    mock = MagicMock()

    async def mock_get(*args, **kwargs):
        return response

    mock.get = mock_get
    mock.aclose = AsyncMock()
    return mock


@pytest.mark.asyncio
class TestXListScraper:
    """Test XListScraper (async)."""

    @pytest.fixture(scope="class")
    def storage(self):
        return MagicMock(name="intel_storage")

    async def test_source_name(self, storage):
        from intelligence.sources.x_list import XListScraper

        scraper = XListScraper(storage, bearer_token="test", list_id="123")
        assert scraper.source_name == "x_list"
        await scraper.close()

    async def test_max_tweets_clamped(self, storage):
        """max_tweets clamped to API limit of 100."""
        from intelligence.sources.x_list import XListScraper

        scraper = XListScraper(storage, max_tweets=500)
        assert scraper.max_tweets == 100
        await scraper.close()

    async def test_missing_bearer_returns_empty(self, storage):
        """No bearer token → empty list, no error."""
        from intelligence.sources.x_list import XListScraper

        scraper = XListScraper(storage, bearer_token=None, list_id="123")
        items = await scraper.scrape()
        assert items == []
        await scraper.close()

    async def test_missing_list_id_returns_empty(self, storage):
        """No list_id → empty list, no error."""
        from intelligence.sources.x_list import XListScraper

        scraper = XListScraper(storage, bearer_token="test", list_id=None)
        items = await scraper.scrape()
        assert items == []
        await scraper.close()

    async def test_successful_scrape(self, storage):
        """Successful API response maps tweets to IntelItems."""
        from intelligence.sources.x_list import XListScraper

        api_response = {
            "data": [
                {
                    "id": "111",
                    "text": "Hello from X! This is a test tweet with some content.",
                    "author_id": "user1",
                    "created_at": "2026-03-12T10:00:00Z",
                    "public_metrics": {"like_count": 5},
                },
                {
                    "id": "222",
                    "text": "Another tweet here.",
                    "author_id": "user2",
                    "created_at": "2026-03-12T11:00:00Z",
                    "public_metrics": {"like_count": 10},
                },
            ],
            "includes": {
                "users": [
                    {"id": "user1", "username": "alice"},
                    {"id": "user2", "username": "bob"},
                ]
            },
        }

        mock_response = httpx.Response(
            status_code=200,
            json=api_response,
            request=httpx.Request("GET", "https://api.twitter.com/2/lists/123/tweets"),
        )

        scraper = XListScraper(storage, bearer_token="test-token", list_id="123")
        scraper._client = _make_mock_client(mock_response)

        items = await scraper.scrape()
        assert len(items) == 2

        assert items[0].source == "x_list"
        assert items[0].title.startswith("alice:")
        assert "https://x.com/alice/status/111" == items[0].url
        assert items[0].tags == ["alice"]
        assert items[0].published is not None

        assert items[1].url == "https://x.com/bob/status/222"
        assert items[1].tags == ["bob"]

        await scraper.close()

    async def test_empty_tweet_text_skipped(self, storage):
        """Tweets with empty text are skipped."""
        from intelligence.sources.x_list import XListScraper

        api_response = {
            "data": [
                {
                    "id": "111",
                    "text": "",
                    "author_id": "user1",
                    "created_at": "2026-03-12T10:00:00Z",
                },
                {
                    "id": "222",
                    "text": "   ",
                    "author_id": "user1",
                    "created_at": "2026-03-12T10:00:00Z",
                },
                {
                    "id": "333",
                    "text": "Valid tweet",
                    "author_id": "user1",
                    "created_at": "2026-03-12T10:00:00Z",
                },
            ],
            "includes": {"users": [{"id": "user1", "username": "alice"}]},
        }

        mock_response = httpx.Response(
            status_code=200,
            json=api_response,
            request=httpx.Request("GET", "https://api.twitter.com/2/lists/123/tweets"),
        )

        scraper = XListScraper(storage, bearer_token="test-token", list_id="123")
        scraper._client = _make_mock_client(mock_response)

        items = await scraper.scrape()
        assert len(items) == 1
        assert "Valid tweet" in items[0].summary

        await scraper.close()

    async def test_no_data_returns_empty(self, storage):
        """API returns no data field → empty list."""
        from intelligence.sources.x_list import XListScraper

        mock_response = httpx.Response(
            status_code=200,
            json={"data": [], "includes": {"users": []}},
            request=httpx.Request("GET", "https://api.twitter.com/2/lists/123/tweets"),
        )

        scraper = XListScraper(storage, bearer_token="test-token", list_id="123")
        scraper._client = _make_mock_client(mock_response)

        items = await scraper.scrape()
        assert items == []

        await scraper.close()

    async def test_title_truncation(self, storage):
        """Long tweet text truncated in title to 80 chars."""
        from intelligence.sources.x_list import XListScraper

        long_text = "A" * 200
        api_response = {
            "data": [
                {
                    "id": "111",
                    "text": long_text,
                    "author_id": "u1",
                    "created_at": "2026-03-12T10:00:00Z",
                }
            ],
            "includes": {"users": [{"id": "u1", "username": "alice"}]},
        }

        mock_response = httpx.Response(
            status_code=200,
            json=api_response,
            request=httpx.Request("GET", "https://api.twitter.com/2/lists/123/tweets"),
        )

        scraper = XListScraper(storage, bearer_token="test", list_id="123")
        scraper._client = _make_mock_client(mock_response)

        items = await scraper.scrape()
        assert len(items) == 1
        # Title = "alice: " + 80 chars of text
        assert len(items[0].title) <= len("alice: ") + 80
        # Summary has full text
        assert items[0].summary == long_text

        await scraper.close()


class TestIntelSourceEnum:
    """Test X_LIST added to IntelSource."""

    def test_x_list_member(self):
        from shared_types import IntelSource

        assert IntelSource.X_LIST == "x_list"
        assert "x_list" in [m.value for m in IntelSource]
