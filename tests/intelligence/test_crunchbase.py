"""Tests for Crunchbase scraper."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from intelligence.sources.crunchbase import CrunchbaseScraper
from shared_types import IntelSource

SAMPLE_RESPONSE = {
    "entities": [
        {
            "uuid": "abc-123",
            "properties": {
                "funded_organization_identifier": {"value": "CoolAI"},
                "investment_type": "series_a",
                "money_raised": {"value": 15000000, "currency": "USD"},
                "investor_identifiers": [
                    {"value": "Sequoia Capital"},
                    {"value": "Andreessen Horowitz"},
                ],
                "short_description": "AI-powered dev tools startup.",
                "announced_on": "2026-02-25",
            },
        },
        {
            "uuid": "def-456",
            "properties": {
                "funded_organization_identifier": {"value": "DevToolCo"},
                "investment_type": "seed",
                "money_raised": {},
                "investor_identifiers": [],
                "short_description": "",
                "announced_on": "2026-02-24",
            },
        },
    ]
}


class TestCrunchbaseScraper:
    @pytest.fixture(scope="class")
    def storage(self):
        return MagicMock(name="intel_storage")

    @pytest.fixture
    def scraper(self, storage):
        return CrunchbaseScraper(storage, api_key="test-key-123")

    def test_source_name(self, scraper):
        assert scraper.source_name == IntelSource.CRUNCHBASE

    def test_no_api_key_returns_empty(self, storage):
        with patch.dict(os.environ, {}, clear=True):
            # Ensure CRUNCHBASE_API_KEY not set
            os.environ.pop("CRUNCHBASE_API_KEY", None)
            scraper = CrunchbaseScraper(storage, api_key="")

        assert scraper.api_key == ""

    @pytest.mark.asyncio
    async def test_scrape_no_key(self, storage):
        scraper = CrunchbaseScraper(storage, api_key="")
        scraper.api_key = ""
        items = await scraper.scrape()
        assert items == []

    @pytest.mark.asyncio
    async def test_scrape_valid_response(self, scraper):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = SAMPLE_RESPONSE

        scraper.client = AsyncMock()
        scraper.client.post = AsyncMock(return_value=mock_resp)

        items = await scraper.scrape()

        assert len(items) == 2
        assert items[0].source == IntelSource.CRUNCHBASE
        assert "CoolAI" in items[0].title
        assert "$15,000,000" in items[0].title
        assert "series_a" in items[0].title
        assert "Sequoia Capital" in items[0].summary
        assert items[0].published is not None
        assert "funding" in items[0].tags

        # Second item has undisclosed amount
        assert "DevToolCo" in items[1].title
        assert "undisclosed" in items[1].title

    @pytest.mark.asyncio
    async def test_scrape_401_invalid_key(self, scraper):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("401", request=MagicMock(), response=mock_resp)
        )

        scraper.client = AsyncMock()
        scraper.client.post = AsyncMock(return_value=mock_resp)

        items = await scraper.scrape()
        assert items == []

    @pytest.mark.asyncio
    async def test_scrape_request_error(self, scraper):
        scraper.client = AsyncMock()
        scraper.client.post = AsyncMock(side_effect=httpx.RequestError("connection failed"))

        items = await scraper.scrape()
        assert items == []

    @pytest.mark.asyncio
    async def test_scrape_empty_entities(self, scraper):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"entities": []}

        scraper.client = AsyncMock()
        scraper.client.post = AsyncMock(return_value=mock_resp)

        items = await scraper.scrape()
        assert items == []

    def test_parse_missing_uuid(self, scraper):
        data = {"entities": [{"uuid": "", "properties": {}}]}
        items = scraper._parse_response(data)
        assert items == []

    def test_parse_missing_fields_graceful(self, scraper):
        data = {
            "entities": [
                {
                    "uuid": "xyz-789",
                    "properties": {
                        "investment_type": "pre_seed",
                    },
                }
            ]
        }
        items = scraper._parse_response(data)
        assert len(items) == 1
        assert "Unknown" in items[0].title
        assert "undisclosed" in items[0].title
