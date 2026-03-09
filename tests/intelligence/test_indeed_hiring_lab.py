"""Tests for Indeed Hiring Lab scraper."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from intelligence.sources.indeed_hiring_lab import IndeedHiringLabScraper
from shared_types import IntelSource

SAMPLE_CSV = """\
date,jobcountry,indeed_job_postings_index,variable,display_name
2026-02-01,US,100.0,total postings,Software Development
2026-02-02,US,101.0,total postings,Software Development
2026-02-03,US,102.0,total postings,Software Development
2026-02-04,US,103.0,total postings,Software Development
2026-02-05,US,104.0,total postings,Software Development
2026-02-06,US,105.0,total postings,Software Development
2026-02-07,US,106.0,total postings,Software Development
2026-02-08,US,107.0,total postings,Software Development
2026-02-09,US,108.0,total postings,Software Development
2026-02-10,US,109.0,total postings,Software Development
2026-02-11,US,110.0,total postings,Software Development
2026-02-12,US,111.0,total postings,Software Development
2026-02-13,US,112.0,total postings,Software Development
2026-02-14,US,120.0,total postings,Software Development
2026-02-15,US,121.0,total postings,Software Development
2026-02-16,US,122.0,total postings,Software Development
2026-02-17,US,123.0,total postings,Software Development
2026-02-18,US,124.0,total postings,Software Development
2026-02-19,US,125.0,total postings,Software Development
2026-02-20,US,126.0,total postings,Software Development
2026-02-21,US,127.0,total postings,Software Development
"""

SAMPLE_CSV_NO_CHANGE = """\
date,jobcountry,indeed_job_postings_index,variable,display_name
2026-02-01,US,100.0,total postings,Nursing
2026-02-02,US,100.1,total postings,Nursing
2026-02-03,US,100.0,total postings,Nursing
2026-02-04,US,100.1,total postings,Nursing
2026-02-05,US,100.0,total postings,Nursing
2026-02-06,US,100.1,total postings,Nursing
2026-02-07,US,100.0,total postings,Nursing
2026-02-08,US,100.1,total postings,Nursing
2026-02-09,US,100.0,total postings,Nursing
2026-02-10,US,100.1,total postings,Nursing
2026-02-11,US,100.0,total postings,Nursing
2026-02-12,US,100.1,total postings,Nursing
2026-02-13,US,100.0,total postings,Nursing
2026-02-14,US,100.1,total postings,Nursing
2026-02-15,US,100.0,total postings,Nursing
2026-02-16,US,100.1,total postings,Nursing
2026-02-17,US,100.0,total postings,Nursing
2026-02-18,US,100.1,total postings,Nursing
2026-02-19,US,100.0,total postings,Nursing
2026-02-20,US,100.1,total postings,Nursing
2026-02-21,US,100.0,total postings,Nursing
"""


class TestIndeedHiringLabScraper:
    @pytest.fixture(scope="class")
    def storage(self):
        return MagicMock(name="intel_storage")

    @pytest.fixture
    def scraper(self, storage):
        return IndeedHiringLabScraper(storage)

    def test_source_name(self, scraper):
        assert scraper.source_name == IntelSource.INDEED_HIRING_LAB

    def test_default_config(self, scraper):
        assert scraper.change_threshold == 5.0
        assert scraper.max_items == 8

    @pytest.mark.asyncio
    async def test_scrape_with_significant_change(self, scraper):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.text = SAMPLE_CSV

        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(return_value=mock_resp)

        items = await scraper.scrape()

        assert len(items) >= 1
        assert items[0].source == IntelSource.INDEED_HIRING_LAB
        assert "Software Development" in items[0].title
        assert "labor-market" in items[0].tags

    @pytest.mark.asyncio
    async def test_scrape_filters_below_threshold(self, scraper):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.text = SAMPLE_CSV_NO_CHANGE

        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(return_value=mock_resp)

        items = await scraper.scrape()
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_scrape_empty_csv(self, scraper):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.text = "date,jobcountry,indeed_job_postings_index,variable,display_name\n"

        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(return_value=mock_resp)

        items = await scraper.scrape()
        assert items == []

    @pytest.mark.asyncio
    async def test_scrape_fetch_error(self, scraper):
        import httpx

        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(side_effect=httpx.RequestError("timeout"))

        items = await scraper.scrape()
        assert items == []

    @pytest.mark.asyncio
    async def test_max_items_cap(self, storage):
        scraper = IndeedHiringLabScraper(storage, max_items=1)

        # Build CSV with multiple sectors showing big changes
        lines = ["date,jobcountry,indeed_job_postings_index,variable,display_name"]
        for sector in ["Tech", "Finance"]:
            for day in range(1, 22):
                val = 100.0 if day <= 14 else 150.0
                lines.append(f"2026-02-{day:02d},US,{val},total postings,{sector}")
        csv_text = "\n".join(lines)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.text = csv_text

        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(return_value=mock_resp)

        items = await scraper.scrape()
        assert len(items) <= 1
