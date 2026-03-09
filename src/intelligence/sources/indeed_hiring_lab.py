"""Indeed Hiring Lab scraper — sector job posting trend data from public CSV."""

import csv
import io
from collections import defaultdict
from datetime import datetime, timedelta

import httpx
import structlog

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from retry_utils import http_retry
from shared_types import IntelSource

logger = structlog.get_logger().bind(source="indeed_hiring_lab")

CSV_URL = (
    "https://raw.githubusercontent.com/hiring-lab/job_postings_tracker"
    "/master/US/job_postings_by_sector_US.csv"
)


class IndeedHiringLabScraper(BaseScraper):
    """Scrape Indeed Hiring Lab public CSV for sector job posting trends."""

    def __init__(
        self,
        storage: IntelStorage,
        csv_url: str = CSV_URL,
        change_threshold: float = 5.0,
        max_items: int = 8,
    ):
        super().__init__(storage)
        self.csv_url = csv_url
        self.change_threshold = change_threshold
        self.max_items = max_items

    @property
    def source_name(self) -> str:
        return IntelSource.INDEED_HIRING_LAB

    @http_retry(exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.RequestError))
    async def scrape(self) -> list[IntelItem]:
        try:
            response = await self.client.get(self.csv_url)
            response.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning("indeed.fetch_failed", error=str(e))
            return []

        return self._parse_csv(response.text)

    def _parse_csv(self, text: str) -> list[IntelItem]:
        reader = csv.DictReader(io.StringIO(text))

        # Collect rows per sector, filter to total postings
        sector_data: dict[str, list[tuple[datetime, float]]] = defaultdict(list)

        for row in reader:
            variable = row.get("variable", "")
            if variable != "total postings":
                continue

            try:
                date = datetime.strptime(row["date"], "%Y-%m-%d")
                value = float(row["indeed_job_postings_index"])
                display = row.get("display_name", variable)
            except (KeyError, ValueError):
                continue

            sector_data[display].append((date, value))

        if not sector_data:
            logger.info("indeed.no_data")
            return []

        # Determine recent/prior week windows from latest date across all sectors
        all_dates = [d for entries in sector_data.values() for d, _ in entries]
        latest = max(all_dates)
        recent_start = latest - timedelta(days=7)
        prior_start = recent_start - timedelta(days=7)

        items: list[IntelItem] = []

        for sector, entries in sector_data.items():
            recent = [v for d, v in entries if d > recent_start]
            prior = [v for d, v in entries if prior_start < d <= recent_start]

            if not recent or not prior:
                continue

            recent_avg = sum(recent) / len(recent)
            prior_avg = sum(prior) / len(prior)

            if prior_avg == 0:
                continue

            pct_change = ((recent_avg - prior_avg) / prior_avg) * 100

            if abs(pct_change) < self.change_threshold:
                continue

            direction = "up" if pct_change > 0 else "down"
            items.append(
                IntelItem(
                    source=self.source_name,
                    title=f"Indeed: {sector} job postings {direction} {abs(pct_change):.1f}% WoW",
                    url=f"{self.csv_url}#sector={sector.replace(' ', '-').lower()}",
                    summary=(
                        f"{sector} sector job postings index moved from "
                        f"{prior_avg:.1f} to {recent_avg:.1f} "
                        f"({pct_change:+.1f}% week-over-week)."
                    ),
                    published=latest,
                    tags=["labor-market", "hiring", sector.lower().replace(" ", "-")][:5],
                )
            )

        # Sort by absolute change descending, cap at max_items
        items.sort(key=lambda x: abs(float(x.title.split()[-2].rstrip("%"))), reverse=True)
        items = items[: self.max_items]

        logger.info("indeed.scraped", count=len(items))
        return items
