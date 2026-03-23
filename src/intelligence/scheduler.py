"""Job scheduling for intelligence gathering."""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import structlog
import structlog.contextvars
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from graceful import graceful_context
from observability import metrics

from .health import ScraperHealthTracker
from .job_registry import build_job_specs, register_jobs
from .runners import (
    RecommendationRunner,
    ResearchRunner,
    RunnerContext,
    refresh_capability_model,
    run_autonomous_actions,
    run_github_repo_poll,
    run_goal_intel_matching,
    run_heartbeat,
    run_memory_consolidation,
    run_signal_detection,
    run_trending_radar,
    run_weekly_summary,
)
from .scraper import IntelStorage
from .scraper_factory import ScraperFactory
from .watchlist_pipeline import (
    create_company_movement_pipeline,
    create_hiring_pipeline,
    create_regulatory_pipeline,
)

logger = structlog.get_logger().bind(source="scheduler")


def _parse_cron(expr: str, defaults: Optional[dict] = None) -> CronTrigger:
    """Parse cron expression string into CronTrigger."""
    d = defaults or {"minute": "0", "hour": "6", "day": "*", "month": "*", "day_of_week": "*"}
    parts = expr.split()
    return CronTrigger(
        minute=parts[0] if len(parts) > 0 else d.get("minute", "0"),
        hour=parts[1] if len(parts) > 1 else d.get("hour", "6"),
        day=parts[2] if len(parts) > 2 else d.get("day", "*"),
        month=parts[3] if len(parts) > 3 else d.get("month", "*"),
        day_of_week=parts[4] if len(parts) > 4 else d.get("day_of_week", "*"),
    )


class IntelScheduler:
    """Manages scheduled intelligence gathering jobs. Delegates to extracted modules."""

    def __init__(
        self,
        storage: IntelStorage,
        config: Optional[dict] = None,
        journal_storage=None,
        embeddings=None,
        full_config: Optional[dict] = None,
        on_error: Optional[Callable] = None,
    ):
        self.storage = storage
        self.config = config or {}
        self.journal_storage = journal_storage
        self.embeddings = embeddings
        self.full_config = full_config or {}
        self.on_error = on_error
        self.scheduler = BackgroundScheduler()
        self._scrapers: list = []
        self._entity_extraction_runner = None
        self.intel_embedding_mgr = None

        self._health = ScraperHealthTracker(storage.db_path)
        self._research = ResearchRunner(storage, journal_storage, embeddings, self.full_config)
        self._recommendations = RecommendationRunner(storage, journal_storage, self.full_config)

        self._ctx = RunnerContext(
            storage=storage,
            full_config=self.full_config,
            journal_storage=journal_storage,
            embeddings=embeddings,
        )

        # Lazy-init pipeline instances
        self._company_pipeline = None
        self._hiring_pipeline = None
        self._regulatory_pipeline = None

    # --- Scraper init + async execution (stays here: tightly coupled to _health/metrics) ---

    def _init_scrapers(self):
        factory = ScraperFactory(self.storage, self.config, self.full_config)
        self._scrapers, self.intel_embedding_mgr, self._feed_health = factory.create_all()
        self._ctx.intel_embedding_mgr = self.intel_embedding_mgr

    async def _run_async(self) -> dict:
        """Run all scrapers concurrently."""
        run_id = uuid.uuid4().hex[:8]
        structlog.contextvars.bind_contextvars(run_id=run_id)

        try:
            self._init_scrapers()
            results = {}
            dedup_threshold = self.config.get("semantic_dedup_threshold", 0.92)

            async def run_scraper(scraper):
                source = scraper.source_name
                if self._health.should_skip(source):
                    logger.info("scraper_skipped_backoff", source=source)
                    return source, {"skipped": "backoff"}
                try:
                    import time as _time

                    t0 = _time.time()
                    with metrics.timer("scrape_duration"):
                        items = await asyncio.wait_for(scraper.scrape(), timeout=60.0)
                        new_count, deduped_count = await scraper.save_items(
                            items, dedup_threshold=dedup_threshold
                        )
                    elapsed = _time.time() - t0

                    self._health.record_success(
                        source,
                        items_scraped=len(items),
                        items_new=new_count,
                        duration_s=round(elapsed, 2),
                        items_deduped=deduped_count,
                    )
                    with graceful_context(
                        "graceful.scheduler.log_event", log_level="debug", exc_types=(ImportError,)
                    ):
                        from user_state_store import log_event

                        log_event(
                            "scraper_run", metadata={"source": source, "items_added": new_count}
                        )
                    metrics.counter("scraper_success")
                    metrics.counter("scraper_items_new", new_count)

                    return source, {
                        "scraped": len(items),
                        "new": new_count,
                        "deduped": deduped_count,
                    }
                except asyncio.TimeoutError:
                    self._health.record_failure(source, "timeout")
                    metrics.counter("scraper_failure")
                    return source, {"error": "timeout"}
                except Exception as e:
                    error_str = str(e)
                    logger.warning(
                        "scraper_failed",
                        source=source,
                        error=error_str,
                        error_type=type(e).__name__,
                    )
                    self._health.record_failure(source, error_str)
                    metrics.counter("scraper_failure")
                    return source, {"error": error_str}
                finally:
                    await scraper.close()

            tasks = [run_scraper(s) for s in self._scrapers]
            completed = await asyncio.gather(*tasks, return_exceptions=True)

            for result in completed:
                if isinstance(result, tuple):
                    name, data = result
                    results[name] = data
                elif isinstance(result, Exception):
                    logger.warning(
                        "scraper_gather_exception",
                        error=str(result),
                        error_type=type(result).__name__,
                    )
                    metrics.counter("scraper_failure")
                    results["unknown"] = {"error": str(result)}

            # Invalidate greeting caches after scrape batch
            try:
                from advisor.context_cache import ContextCache

                cache_db = self.storage.db_path.parent / "context_cache.db"
                cache = ContextCache(cache_db)
                cache.invalidate_by_prefix("greeting_v1_")
            except Exception as e:
                logger.warning("greeting_cache_invalidate_failed", error=str(e))

            return results
        finally:
            structlog.contextvars.unbind_contextvars("run_id")

    def run_now(self) -> dict:
        """Run async scrapers from sync context."""
        return asyncio.run(self._run_async())

    # --- Entity extraction (coupled to scheduler lifecycle) ---

    def _get_entity_scheduler(self):
        if self._entity_extraction_runner is False:
            return None
        if self._entity_extraction_runner is not None:
            return self._entity_extraction_runner

        entity_config = self.full_config.get("entity_extraction", {})
        if entity_config.get("enabled", True) is False:
            self._entity_extraction_runner = False
            return None

        try:
            from intelligence.entity_extractor import EntityExtractor, ExtractionScheduler
            from intelligence.entity_store import EntityStore
            from llm import create_cheap_provider

            entity_store = EntityStore(self.storage.db_path)
            extractor = EntityExtractor(
                llm=create_cheap_provider(),
                storage=self.storage,
                entity_store=entity_store,
                batch_size=entity_config.get("batch_size", 10),
                max_content_chars=entity_config.get("max_content_chars", 2000),
                entity_types=entity_config.get("entity_types"),
                relationship_types=entity_config.get("relationship_types"),
            )
            self._entity_extraction_runner = ExtractionScheduler(
                extractor,
                entity_store,
                batch_size=entity_config.get("batch_size", 10),
            )
        except Exception as e:
            logger.warning("entity_extraction_init_failed", error=str(e))
            self._entity_extraction_runner = False
            return None

        return self._entity_extraction_runner

    def run_entity_extraction(self):
        runner = self._get_entity_scheduler()
        if not runner:
            return {"status": "disabled"}
        result = asyncio.run(runner.run_extraction())
        logger.info("entity_extraction.complete", **result.__dict__)
        return result.__dict__

    # --- Error handler ---

    def _default_error_handler(self, event):
        logger.error(
            "job_error",
            job_id=event.job_id,
            exception=str(event.exception),
            traceback=event.traceback,
        )
        status_path = Path("~/.coach/last_run_status.json").expanduser()
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_data = {
            "status": "error",
            "job_id": event.job_id,
            "error": str(event.exception),
            "timestamp": datetime.now().isoformat(),
        }
        status_path.write_text(json.dumps(status_data, indent=2))

        if self.on_error:
            try:
                self.on_error(event)
            except Exception as e:
                logger.error("Error in custom on_error callback: %s", e)

    # --- Watchlist pipeline delegates ---

    def run_company_movement_pipeline(self) -> dict:
        if not self._company_pipeline:
            self._company_pipeline = create_company_movement_pipeline(
                self.storage, self.full_config
            )
        return self._company_pipeline.run()

    def run_hiring_activity_pipeline(self) -> dict:
        if not self._hiring_pipeline:
            self._hiring_pipeline = create_hiring_pipeline(self.storage, self.full_config)
        return self._hiring_pipeline.run()

    def run_regulatory_pipeline(self) -> dict:
        if not self._regulatory_pipeline:
            self._regulatory_pipeline = create_regulatory_pipeline(self.storage, self.full_config)
        return self._regulatory_pipeline.run()

    # --- Runner delegates ---

    def run_signal_detection(self) -> list:
        return run_signal_detection(self._ctx)

    def run_autonomous_actions(self) -> list:
        return run_autonomous_actions(self._ctx)

    def refresh_capability_model(self) -> dict:
        return refresh_capability_model(self._ctx)

    def run_github_repo_poll(self) -> dict:
        return run_github_repo_poll(self._ctx)

    def run_goal_intel_matching(self):
        return run_goal_intel_matching(self._ctx)

    def run_heartbeat(self):
        return run_heartbeat(self._ctx)

    def run_trending_radar(self):
        return run_trending_radar(self._ctx)

    def run_weekly_summary(self):
        return run_weekly_summary(self._ctx)

    def run_memory_consolidation(self):
        return run_memory_consolidation(self._ctx)

    # --- Research + recommendation delegates ---

    def run_research_now(
        self, topic: Optional[str] = None, dossier_id: Optional[str] = None
    ) -> list[dict]:
        return self._research.run(topic=topic, dossier_id=dossier_id)

    def get_research_topics(self) -> list[dict]:
        return self._research.get_topics()

    def list_research_dossiers(self, include_archived: bool = False, limit: int = 50) -> list[dict]:
        return self._research.list_dossiers(include_archived=include_archived, limit=limit)

    def create_research_dossier(self, **kwargs) -> dict | None:
        return self._research.create_dossier(**kwargs)

    def get_research_dossier(self, dossier_id: str) -> dict | None:
        return self._research.get_dossier(dossier_id)

    def run_recommendations_now(self) -> dict:
        return self._recommendations.run()

    # --- Scheduling ---

    def start(self, cron_expr: str = "0 6 * * *"):
        trigger = _parse_cron(cron_expr)
        self.scheduler.add_job(
            self.run_now, trigger=trigger, id="intel_gather", replace_existing=True
        )
        self._schedule_extended_jobs()
        self._schedule_entity_extraction_job()
        self.scheduler.add_listener(self._default_error_handler, EVENT_JOB_ERROR)
        self.scheduler.start()

    def start_with_research(
        self,
        scrape_cron: str = "0 6 * * *",
        research_cron: str = "0 21 * * 0",
    ):
        specs = build_job_specs(self, scrape_cron, research_cron)
        register_jobs(self.scheduler, specs)
        self.scheduler.add_listener(self._default_error_handler, EVENT_JOB_ERROR)
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()

    def _schedule_extended_jobs(self) -> None:
        company_config = self.full_config.get("company_movement", {})
        if company_config.get("enabled", False):
            cron = company_config.get("run_cron", "0 */6 * * *")
            self.scheduler.add_job(
                self.run_company_movement_pipeline,
                trigger=_parse_cron(cron),
                id="company_movement_pipeline",
                replace_existing=True,
            )
            logger.info("company_movement.scheduled", cron=cron)

        hiring_config = self.full_config.get("hiring", {})
        if hiring_config.get("enabled", False):
            cron = hiring_config.get("run_cron", "0 */12 * * *")
            self.scheduler.add_job(
                self.run_hiring_activity_pipeline,
                trigger=_parse_cron(cron),
                id="hiring_activity_pipeline",
                replace_existing=True,
            )
            logger.info("hiring_pipeline.scheduled", cron=cron)

        reg_config = self.full_config.get("regulatory", {})
        if reg_config.get("enabled", False):
            cron = reg_config.get("run_cron", "0 */12 * * *")
            self.scheduler.add_job(
                self.run_regulatory_pipeline,
                trigger=_parse_cron(cron),
                id="regulatory_pipeline",
                replace_existing=True,
            )
            logger.info("regulatory_pipeline.scheduled", cron=cron)

    def _schedule_entity_extraction_job(self) -> None:
        entity_config = self.full_config.get("entity_extraction", {})
        if entity_config.get("enabled", True) is False:
            return

        from apscheduler.triggers.interval import IntervalTrigger

        self.scheduler.add_job(
            self.run_entity_extraction,
            trigger=IntervalTrigger(minutes=entity_config.get("schedule_minutes", 30)),
            id="entity_extraction",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=300,
        )
        logger.info(
            "entity_extraction.scheduled",
            interval_minutes=entity_config.get("schedule_minutes", 30),
        )
