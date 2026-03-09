"""Google Trends scraper — keyword interest spikes via pytrends."""

import asyncio
from datetime import datetime

import structlog

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from shared_types import IntelSource

logger = structlog.get_logger().bind(source="google_trends")


class GoogleTrendsScraper(BaseScraper):
    """Detect interest spikes for configured keywords via Google Trends."""

    def __init__(
        self,
        storage: IntelStorage,
        keywords: list[str] | None = None,
        spike_threshold: float = 20.0,
        timeframe: str = "today 1-m",
        sleep_fn=None,
        batch_delay_seconds: float = 2.0,
    ):
        super().__init__(storage)
        self.keywords = keywords or ["AI agents", "LLM fine-tuning"]
        self.spike_threshold = spike_threshold
        self.timeframe = timeframe
        self.sleep_fn = sleep_fn or asyncio.sleep
        self.batch_delay_seconds = batch_delay_seconds

    @property
    def source_name(self) -> str:
        return IntelSource.GOOGLE_TRENDS

    async def scrape(self) -> list[IntelItem]:
        try:
            from pytrends.request import TrendReq
        except ImportError:
            logger.warning("google_trends.pytrends_not_installed")
            return []

        items: list[IntelItem] = []

        # Batch keywords in groups of 5 (pytrends limit)
        batches = [self.keywords[i : i + 5] for i in range(0, len(self.keywords), 5)]

        for i, batch in enumerate(batches):
            if i > 0 and self.batch_delay_seconds > 0:
                await self.sleep_fn(self.batch_delay_seconds)

            try:
                batch_items = await asyncio.to_thread(self._query_batch, batch, TrendReq)
                items.extend(batch_items)
            except Exception as e:
                logger.warning("google_trends.batch_failed", batch=batch, error=str(e))

        logger.info("google_trends.scraped", count=len(items))
        return items

    def _query_batch(self, keywords: list[str], trend_req_cls) -> list[IntelItem]:
        """Query a batch of keywords (runs in thread)."""
        pytrends = trend_req_cls(hl="en-US", tz=360)
        pytrends.build_payload(keywords, timeframe=self.timeframe)

        df = pytrends.interest_over_time()
        if df is None or df.empty:
            return []

        items: list[IntelItem] = []
        now = datetime.now()

        for kw in keywords:
            if kw not in df.columns:
                continue

            series = df[kw]
            if len(series) < 5:
                continue

            last_val = float(series.iloc[-1])
            mean_4w = (
                float(series.iloc[:-1].tail(4 * 7).mean())
                if len(series) > 7
                else float(series.iloc[:-1].mean())
            )

            delta = last_val - mean_4w

            if delta < self.spike_threshold:
                continue

            items.append(
                IntelItem(
                    source=self.source_name,
                    title=f"Google Trends: '{kw}' interest spiked +{delta:.0f} pts",
                    url=f"https://trends.google.com/trends/explore?q={kw.replace(' ', '%20')}",
                    summary=(
                        f"'{kw}' interest rose from {mean_4w:.0f} to {last_val:.0f} "
                        f"(+{delta:.0f} points on 0-100 scale) over the past week."
                    ),
                    published=now,
                    tags=["trends", "interest-spike", kw.lower().replace(" ", "-")][:5],
                )
            )

        return items
