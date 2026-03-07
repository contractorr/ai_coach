"""Crunchbase scraper — recent funding rounds via REST v4 API."""

import os
from datetime import datetime, timedelta

import httpx
import structlog

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from retry_utils import http_retry
from shared_types import IntelSource

logger = structlog.get_logger().bind(source="crunchbase")

API_URL = "https://api.crunchbase.com/api/v4/searches/funding_rounds"


class CrunchbaseScraper(BaseScraper):
    """Scrape Crunchbase for recent funding rounds in configured categories."""

    def __init__(
        self,
        storage: IntelStorage,
        api_key: str | None = None,
        categories: list[str] | None = None,
        days_back: int = 7,
        max_items: int = 20,
    ):
        super().__init__(storage)
        self.api_key = api_key or os.getenv("CRUNCHBASE_API_KEY", "")
        self.categories = categories or ["artificial-intelligence", "developer-tools"]
        self.days_back = days_back
        self.max_items = max_items

    @property
    def source_name(self) -> str:
        return IntelSource.CRUNCHBASE

    @http_retry(exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.RequestError))
    async def scrape(self) -> list[IntelItem]:
        if not self.api_key:
            logger.warning("crunchbase.no_api_key")
            return []

        since = (datetime.now() - timedelta(days=self.days_back)).strftime("%Y-%m-%d")

        payload = {
            "field_ids": [
                "identifier",
                "short_description",
                "money_raised",
                "investment_type",
                "announced_on",
                "funded_organization_identifier",
                "investor_identifiers",
            ],
            "query": [
                {
                    "type": "predicate",
                    "field_id": "announced_on",
                    "operator_id": "gte",
                    "values": [since],
                },
                {
                    "type": "predicate",
                    "field_id": "funded_organization_categories",
                    "operator_id": "includes",
                    "values": self.categories,
                },
            ],
            "order": [{"field_id": "announced_on", "sort": "desc"}],
            "limit": self.max_items,
        }

        try:
            response = await self.client.post(
                API_URL,
                params={"user_key": self.api_key},
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning("crunchbase.invalid_api_key")
            else:
                logger.warning("crunchbase.fetch_failed", status=e.response.status_code)
            return []
        except httpx.RequestError as e:
            logger.warning("crunchbase.request_error", error=str(e))
            return []

        return self._parse_response(response.json())

    def _parse_response(self, data: dict) -> list[IntelItem]:
        entities = data.get("entities", [])
        items: list[IntelItem] = []

        for entity in entities:
            props = entity.get("properties", {})

            uuid = entity.get("uuid", "")
            url = f"https://www.crunchbase.com/funding_round/{uuid}" if uuid else ""
            if not url:
                continue

            org_id = props.get("funded_organization_identifier", {})
            org_name = org_id.get("value", "Unknown") if isinstance(org_id, dict) else "Unknown"

            round_type = props.get("investment_type", "unknown")

            money = props.get("money_raised", {})
            if isinstance(money, dict):
                amount = money.get("value")
                currency = money.get("currency", "USD")
                amount_str = f"${amount:,.0f} {currency}" if amount else "undisclosed"
            else:
                amount_str = "undisclosed"

            investors_raw = props.get("investor_identifiers", [])
            if isinstance(investors_raw, list):
                investor_names = [
                    inv.get("value", "") for inv in investors_raw if isinstance(inv, dict)
                ][:3]
            else:
                investor_names = []
            investor_str = ", ".join(investor_names) if investor_names else "undisclosed investors"

            desc = props.get("short_description", "")

            announced = props.get("announced_on", "")
            published = None
            if announced:
                try:
                    published = datetime.strptime(announced, "%Y-%m-%d")
                except ValueError:
                    pass

            title = f"{org_name} raised {amount_str} ({round_type})"
            summary = f"{title}. Investors: {investor_str}."
            if desc:
                summary += f" {desc[:300]}"

            items.append(
                IntelItem(
                    source=self.source_name,
                    title=title,
                    url=url,
                    summary=summary[:500],
                    published=published,
                    tags=["funding", round_type, "startup"][:5],
                )
            )

        logger.info("crunchbase.scraped", count=len(items))
        return items
