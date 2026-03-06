"""Job scheduling for intelligence gathering."""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import structlog
import structlog.contextvars
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from observability import metrics

from .health import RSSFeedHealthTracker, ScraperHealthTracker
from .scraper import IntelStorage
from .sources import (
    AICapabilitiesScraper,
    AIIndexScraper,
    ARCEvalsScraper,
    ArxivScraper,
    CrunchbaseScraper,
    EpochAIScraper,
    EventScraper,
    FrontierEvalsGitHubScraper,
    GitHubIssuesScraper,
    GitHubTrendingScraper,
    GooglePatentsScraper,
    GoogleTrendsScraper,
    HackerNewsScraper,
    IndeedHiringLabScraper,
    METRScraper,
    ProductHuntScraper,
    RedditScraper,
    RSSFeedScraper,
    YCJobsScraper,
)

logger = structlog.get_logger().bind(source="scheduler")


def _parse_cron(expr: str, defaults: Optional[dict] = None) -> CronTrigger:
    """Parse cron expression string into CronTrigger.

    Args:
        expr: 5-field cron expression (min hour day month dow)
        defaults: Optional dict of default values for missing fields
    """
    d = defaults or {"minute": "0", "hour": "6", "day": "*", "month": "*", "day_of_week": "*"}
    parts = expr.split()
    return CronTrigger(
        minute=parts[0] if len(parts) > 0 else d.get("minute", "0"),
        hour=parts[1] if len(parts) > 1 else d.get("hour", "6"),
        day=parts[2] if len(parts) > 2 else d.get("day", "*"),
        month=parts[3] if len(parts) > 3 else d.get("month", "*"),
        day_of_week=parts[4] if len(parts) > 4 else d.get("day_of_week", "*"),
    )


class ResearchRunner:
    """Handles deep research agent initialization and execution."""

    def __init__(self, storage: IntelStorage, journal_storage, embeddings, config: dict):
        self.storage = storage
        self.journal_storage = journal_storage
        self.embeddings = embeddings
        self.config = config

    def _init_agent(self):
        """Initialize research agent if configured."""
        research_config = self.config.get("research", {})
        if not research_config.get("enabled", False):
            return None

        if not self.journal_storage or not self.embeddings:
            logger.warning("Research agent requires journal_storage and embeddings")
            return None

        try:
            from research.agent import DeepResearchAgent

            return DeepResearchAgent(
                journal_storage=self.journal_storage,
                intel_storage=self.storage,
                embeddings=self.embeddings,
                config=self.config,
            )
        except ImportError as e:
            logger.error("Failed to import research agent: %s", e)
            return None

    def run(self, topic: Optional[str] = None) -> list[dict]:
        """Run deep research immediately."""
        agent = self._init_agent()
        if not agent:
            logger.warning("Research agent not available")
            return []

        try:
            return agent.run(specific_topic=topic)
        finally:
            agent.close()

    def get_topics(self) -> list[dict]:
        """Get suggested research topics."""
        agent = self._init_agent()
        if not agent:
            return []

        try:
            return agent.get_suggested_topics()
        finally:
            agent.close()


class RecommendationRunner:
    """Handles recommendation generation and action brief saving."""

    def __init__(self, storage: IntelStorage, journal_storage, config: dict):
        self.storage = storage
        self.journal_storage = journal_storage
        self.config = config

    def run(self) -> dict:
        """Generate recommendations and save action brief."""
        rec_config = self.config.get("recommendations", {})
        if not rec_config.get("enabled", False):
            logger.warning("Recommendations not enabled")
            return {"error": "not_enabled"}

        if not self.journal_storage:
            logger.warning("Journal storage required for recommendations")
            return {"error": "no_journal_storage"}

        try:
            from advisor.engine import AdvisorEngine
            from advisor.rag import RAGRetriever
            from journal import EmbeddingManager, JournalSearch
            from journal.fts import JournalFTSIndex

            paths_config = self.config.get("paths", {})
            chroma_dir = Path(paths_config.get("chroma_dir", "~/coach/chroma")).expanduser()
            journal_dir = Path(paths_config.get("journal_dir", "~/coach/journal")).expanduser()
            embeddings = EmbeddingManager(chroma_dir)
            fts_index = JournalFTSIndex(journal_dir)
            search = JournalSearch(self.journal_storage, embeddings, fts_index=fts_index)
            rag = RAGRetriever(search, self.storage.db_path)

            advisor = AdvisorEngine(rag)

            rec_db = self.storage.db_path.parent / "recommendations"

            max_per_cat = rec_config.get("scoring", {}).get("max_per_category", 3)
            recs = advisor.generate_recommendations(
                "all", rec_db, rec_config, max_items=max_per_cat
            )

            delivery = rec_config.get("delivery", {})
            if "journal" in delivery.get("methods", ["journal"]):
                advisor.generate_action_brief(
                    rec_db,
                    journal_storage=self.journal_storage,
                    save=True,
                )
                logger.info("Action brief saved to journal")

            return {"recommendations": len(recs), "brief_saved": True}

        except Exception as e:
            logger.error("Failed to generate recommendations: %s", e)
            return {"error": str(e)}


class IntelScheduler:
    """Manages scheduled intelligence gathering jobs. Delegates research/recs to runners."""

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

        self._health = ScraperHealthTracker(storage.db_path)
        self._research = ResearchRunner(storage, journal_storage, embeddings, self.full_config)
        self._recommendations = RecommendationRunner(storage, journal_storage, self.full_config)

    def _init_scrapers(self):
        """Initialize async scrapers from config."""
        self._scrapers = []

        enabled = self.config.get("enabled", ["hn_top", "rss_feeds"])

        # Shared per-feed health tracker for all RSS scrapers
        self._feed_health = RSSFeedHealthTracker(self.storage.db_path)

        # Semantic dedup: create shared embedding manager if configured
        intel_embedding_mgr = None
        if self.config.get("semantic_dedup", False):
            try:
                from cli.config import get_paths
                from intelligence.embeddings import IntelEmbeddingManager

                paths = get_paths(self.full_config)
                intel_embedding_mgr = IntelEmbeddingManager(paths["chroma_dir"])
                logger.info("semantic_dedup.enabled")
            except Exception as e:
                logger.warning("semantic_dedup.init_failed", error=str(e))

        # Detect which sources are covered by RSS feeds for dedup
        rss_covered_sources = set()
        if self.config.get("deduplicate_rss_sources", True):
            from intelligence.sources.rss import _detect_source_tag

            for url in self.config.get("rss_feeds", []):
                tag = _detect_source_tag(url)
                if tag:
                    rss_covered_sources.add(tag)

        if "hn_top" in enabled and "hn" not in rss_covered_sources:
            self._scrapers.append(HackerNewsScraper(self.storage))

        config_rss_urls: set[str] = set()
        if "rss_feeds" in enabled:
            for url in self.config.get("rss_feeds", []):
                self._scrapers.append(
                    RSSFeedScraper(self.storage, url, feed_health_tracker=self._feed_health)
                )
                config_rss_urls.add(url)

        # Merge user-added RSS feeds
        try:
            from web.user_store import get_all_user_rss_feeds

            for feed in get_all_user_rss_feeds():
                if feed["url"] not in config_rss_urls:
                    self._scrapers.append(
                        RSSFeedScraper(
                            self.storage,
                            feed["url"],
                            name=feed.get("name"),
                            feed_health_tracker=self._feed_health,
                        )
                    )
                    config_rss_urls.add(feed["url"])
        except Exception:
            pass  # web module may not be available in CLI mode

        if "custom_blogs" in enabled:
            for url in self.config.get("custom_blogs", []):
                self._scrapers.append(
                    RSSFeedScraper(self.storage, url, feed_health_tracker=self._feed_health)
                )

        # GitHub trending
        gh_config = self.config.get("github_trending", {})
        if gh_config.get("enabled", False):
            self._scrapers.append(
                GitHubTrendingScraper(
                    self.storage,
                    languages=gh_config.get("languages", ["python"]),
                    timeframe=gh_config.get("timeframe", "daily"),
                )
            )

        # arXiv (skip if covered by RSS feeds)
        arxiv_config = self.config.get("arxiv", {})
        if (
            "arxiv" in enabled or arxiv_config.get("enabled", False)
        ) and "arxiv" not in rss_covered_sources:
            self._scrapers.append(
                ArxivScraper(
                    self.storage,
                    categories=arxiv_config.get("categories"),
                    max_results=arxiv_config.get("max_results", 30),
                )
            )

        # Reddit (skip if covered by RSS feeds)
        reddit_config = self.config.get("reddit", {})
        if (
            "reddit" in enabled or reddit_config.get("enabled", False)
        ) and "reddit" not in rss_covered_sources:
            self._scrapers.append(
                RedditScraper(
                    self.storage,
                    subreddits=reddit_config.get("subreddits"),
                    limit=reddit_config.get("limit", 25),
                    timeframe=reddit_config.get("timeframe", "day"),
                )
            )

        # Events (confs.tech + RSS)
        events_config = self.full_config.get("events", {})
        if events_config.get("enabled", False):
            # Load profile for location filter
            location = ""
            if events_config.get("location_filter", False):
                try:
                    from profile.storage import ProfileStorage

                    profile_path = self.full_config.get("profile", {}).get(
                        "path", "~/coach/profile.yaml"
                    )
                    ps = ProfileStorage(profile_path)
                    p = ps.load()
                    if p:
                        location = p.location
                except Exception:
                    pass
            self._scrapers.append(
                EventScraper(
                    self.storage,
                    topics=events_config.get("topics"),
                    location_filter=location,
                    rss_feeds=events_config.get("rss_feeds", []),
                )
            )

        # Product Hunt
        ph_config = self.config.get("producthunt", {})
        if "producthunt" in enabled or ph_config.get("enabled", False):
            self._scrapers.append(
                ProductHuntScraper(
                    self.storage,
                    max_items=ph_config.get("max_items", 20),
                )
            )

        # YC Jobs
        yc_config = self.config.get("yc_jobs", {})
        if "yc_jobs" in enabled or yc_config.get("enabled", False):
            self._scrapers.append(
                YCJobsScraper(
                    self.storage,
                    max_items=yc_config.get("max_items", 30),
                )
            )

        # Google Patents
        patents_config = self.config.get("google_patents", {})
        if "google_patents" in enabled or patents_config.get("enabled", False):
            self._scrapers.append(
                GooglePatentsScraper(
                    self.storage,
                    feeds=patents_config.get("feeds"),
                    max_per_feed=patents_config.get("max_per_feed", 15),
                )
            )

        # AI Capabilities (METR, Chatbot Arena, HELM)
        ai_cap_config = self.config.get("ai_capabilities", {})
        if "ai_capabilities" in enabled or ai_cap_config.get("enabled", False):
            self._scrapers.append(
                AICapabilitiesScraper(
                    self.storage,
                    sources=ai_cap_config.get("sources", ["metr", "chatbot_arena", "helm"]),
                    max_items_per_source=ai_cap_config.get("max_items_per_source", 10),
                )
            )

        # GitHub Issues (good-first-issue / help-wanted)
        gh_issues_config = self.full_config.get("projects", {}).get("github_issues", {})
        if gh_issues_config.get("enabled", False):
            langs = gh_issues_config.get("languages")
            if not langs:
                try:
                    from profile.storage import ProfileStorage

                    profile_path = self.full_config.get("profile", {}).get(
                        "path", "~/coach/profile.yaml"
                    )
                    ps = ProfileStorage(profile_path)
                    p = ps.load()
                    if p:
                        langs = p.languages_frameworks[:5]
                except Exception:
                    pass
            self._scrapers.append(
                GitHubIssuesScraper(
                    self.storage,
                    languages=langs or ["python"],
                    labels=gh_issues_config.get("labels", ["good-first-issue", "help-wanted"]),
                    token=gh_issues_config.get("token"),
                )
            )

        # Capability horizon scrapers (always enabled alongside ai_capabilities)
        cap_config = self.config.get("capability_horizon", {})
        if cap_config.get("enabled", False) or (
            "ai_capabilities" in enabled or ai_cap_config.get("enabled", False)
        ):
            self._scrapers.append(METRScraper(self.storage))
            self._scrapers.append(EpochAIScraper(self.storage))
            self._scrapers.append(AIIndexScraper(self.storage))
            self._scrapers.append(ARCEvalsScraper(self.storage))
            gh_token = self.full_config.get("projects", {}).get("github_issues", {}).get("token")
            self._scrapers.append(FrontierEvalsGitHubScraper(self.storage, token=gh_token))

        # Indeed Hiring Lab
        indeed_config = self.config.get("indeed_hiring_lab", {})
        if "indeed_hiring_lab" in enabled or indeed_config.get("enabled", False):
            self._scrapers.append(
                IndeedHiringLabScraper(
                    self.storage,
                    change_threshold=indeed_config.get("change_threshold", 5.0),
                    max_items=indeed_config.get("max_items", 8),
                )
            )

        # Google Trends
        trends_config = self.config.get("google_trends", {})
        if "google_trends" in enabled or trends_config.get("enabled", False):
            self._scrapers.append(
                GoogleTrendsScraper(
                    self.storage,
                    keywords=trends_config.get("keywords"),
                    spike_threshold=trends_config.get("spike_threshold", 20.0),
                    timeframe=trends_config.get("timeframe", "today 1-m"),
                )
            )

        # Crunchbase
        cb_config = self.config.get("crunchbase", {})
        if "crunchbase" in enabled or cb_config.get("enabled", False):
            self._scrapers.append(
                CrunchbaseScraper(
                    self.storage,
                    api_key=cb_config.get("api_key"),
                    categories=cb_config.get("categories"),
                    days_back=cb_config.get("days_back", 7),
                    max_items=cb_config.get("max_items", 20),
                )
            )

        # Store + attach shared embedding manager for semantic dedup + goal matching
        self.intel_embedding_mgr = intel_embedding_mgr
        if intel_embedding_mgr:
            for scraper in self._scrapers:
                scraper.embedding_manager = intel_embedding_mgr

    async def _run_async(self) -> dict:
        """Run all scrapers concurrently."""
        # Generate correlation ID and bind to structlog
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
                    try:
                        from web.user_store import log_event

                        log_event(
                            "scraper_run", metadata={"source": source, "items_added": new_count}
                        )
                    except ImportError:
                        pass
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

            # Invalidate all greeting caches after scrape batch
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

    def _default_error_handler(self, event):
        """Default error handler for APScheduler job failures."""
        logger.error(
            "job_error",
            job_id=event.job_id,
            exception=str(event.exception),
            traceback=event.traceback,
        )

        # Write status file
        status_path = Path("~/.coach/last_run_status.json").expanduser()
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_data = {
            "status": "error",
            "job_id": event.job_id,
            "error": str(event.exception),
            "timestamp": datetime.now().isoformat(),
        }
        status_path.write_text(json.dumps(status_data, indent=2))

        # Call custom handler if provided
        if self.on_error:
            try:
                self.on_error(event)
            except Exception as e:
                logger.error("Error in custom on_error callback: %s", e)

    def start(self, cron_expr: str = "0 6 * * *"):
        """Start scheduled gathering."""
        trigger = _parse_cron(cron_expr)
        self.scheduler.add_job(
            self.run_now,
            trigger=trigger,
            id="intel_gather",
            replace_existing=True,
        )
        self.scheduler.add_listener(self._default_error_handler, EVENT_JOB_ERROR)
        self.scheduler.start()

    def stop(self):
        """Stop scheduler."""
        self.scheduler.shutdown()

    # Delegate research methods
    def run_research_now(self, topic: Optional[str] = None) -> list[dict]:
        """Run deep research immediately."""
        return self._research.run(topic=topic)

    def get_research_topics(self) -> list[dict]:
        """Get suggested research topics."""
        return self._research.get_topics()

    # Delegate recommendation methods
    def run_recommendations_now(self) -> dict:
        """Run recommendation generation and save action brief."""
        return self._recommendations.run()

    # --- Signal detection + autonomous actions ---

    def run_signal_detection(self) -> list:
        """Run signal detection across all data sources."""
        if not self.journal_storage:
            logger.warning("Signal detection requires journal_storage")
            return []
        try:
            from advisor.signals import SignalDetector

            db_path = self.storage.db_path
            detector = SignalDetector(self.journal_storage, db_path, self.full_config)
            signals = detector.detect_all()
            logger.info("signal_detection_complete", count=len(signals))
            return signals
        except Exception as e:
            logger.error("signal_detection_failed", error=str(e))
            return []

    def run_autonomous_actions(self) -> list:
        """Run autonomous actions based on current signals."""
        if not self.journal_storage:
            logger.warning("Autonomous actions require journal_storage")
            return []
        try:
            from advisor.autonomous import AutonomousActionEngine
            from advisor.signals import SignalStore

            db_path = self.storage.db_path
            store = SignalStore(db_path)
            active_signals = store.get_active(limit=20)

            # Reconstruct Signal objects from stored data
            from advisor.signals import Signal, SignalType

            signals = []
            for s in active_signals:
                try:
                    signals.append(
                        Signal(
                            type=SignalType(s["type"]),
                            severity=s["severity"],
                            title=s["title"],
                            detail=s.get("detail", ""),
                            suggested_actions=s.get("suggested_actions", []),
                            evidence=s.get("evidence", []),
                        )
                    )
                except (ValueError, KeyError):
                    continue

            engine = AutonomousActionEngine(
                self.journal_storage, db_path, self.full_config, self.embeddings
            )
            results = engine.process_signals(signals)
            logger.info("autonomous_actions_complete", count=len(results))
            return results
        except Exception as e:
            logger.error("autonomous_actions_failed", error=str(e))
            return []

    def refresh_capability_model(self) -> dict:
        """Run capability scrapers and refresh the CapabilityHorizonModel."""
        from intelligence.capability_model import CapabilityHorizonModel
        from intelligence.sources.ai_capabilities import (
            AIIndexScraper,
            ARCEvalsScraper,
            EpochAIScraper,
            FrontierEvalsGitHubScraper,
            METRScraper,
        )

        async def _run():
            scrapers = [
                METRScraper(self.storage),
                EpochAIScraper(self.storage),
                AIIndexScraper(self.storage),
                ARCEvalsScraper(self.storage),
                FrontierEvalsGitHubScraper(self.storage),
            ]
            all_items = []
            for scraper in scrapers:
                try:
                    items = await asyncio.wait_for(scraper.scrape(), timeout=60.0)
                    all_items.extend(items)
                except Exception as e:
                    logger.warning("cap_scraper_failed", source=scraper.source_name, error=str(e))
                finally:
                    await scraper.close()
            return all_items

        try:
            items = asyncio.run(_run())
        except Exception as e:
            logger.error("capability_model_scrape_failed", error=str(e))
            items = []

        model = CapabilityHorizonModel(self.storage.db_path)
        model.refresh(items)

        updated = sum(1 for d in model.domains if d.last_updated)
        fallback = len(model.domains) - updated if model.domains else 0
        logger.info(
            "capability_model_refreshed",
            total_items=len(items),
            domains_updated=len(model.domains),
            domains_fallback=fallback,
        )
        return {"items_scraped": len(items), "domains": len(model.domains)}

    def start_with_research(
        self,
        scrape_cron: str = "0 6 * * *",
        research_cron: str = "0 21 * * 0",
    ):
        """Start scheduler with both scraping and research jobs."""
        # Add scraping job
        scrape_trigger = _parse_cron(scrape_cron)
        self.scheduler.add_job(
            self.run_now,
            trigger=scrape_trigger,
            id="intel_gather",
            replace_existing=True,
        )

        # Add capability model refresh on same schedule as scraping
        cap_config = self.config.get("capability_horizon", {})
        ai_cap_config = self.config.get("ai_capabilities", {})
        enabled_sources = self.config.get("enabled", [])
        if (
            cap_config.get("enabled", False)
            or "ai_capabilities" in enabled_sources
            or ai_cap_config.get("enabled", False)
        ):
            self.scheduler.add_job(
                self.refresh_capability_model,
                trigger=_parse_cron(scrape_cron),
                id="refresh_capability_model",
                replace_existing=True,
            )
            logger.info("Capability model refresh job scheduled: %s", scrape_cron)

        # Add research job if enabled
        research_config = self.full_config.get("research", {})
        if research_config.get("enabled", False):
            research_trigger = _parse_cron(
                research_cron,
                defaults={
                    "minute": "0",
                    "hour": "21",
                    "day": "*",
                    "month": "*",
                    "day_of_week": "0",
                },
            )
            self.scheduler.add_job(
                self.run_research_now,
                trigger=research_trigger,
                id="deep_research",
                replace_existing=True,
            )
            logger.info("Research job scheduled: %s", research_cron)

        # Add recommendations job if enabled
        rec_config = self.full_config.get("recommendations", {})
        if rec_config.get("enabled", False):
            rec_cron = rec_config.get("delivery", {}).get("schedule", "0 8 * * 0")
            self._add_recommendations_job(rec_cron)

        # Add signal detection + autonomous actions if agent enabled
        agent_config = self.full_config.get("agent", {})
        if agent_config.get("enabled", False):
            signal_cron = agent_config.get("signals", {}).get("schedule", "0 9 * * *")
            signal_trigger = _parse_cron(signal_cron)
            self.scheduler.add_job(
                self.run_signal_detection,
                trigger=signal_trigger,
                id="signal_detection",
                replace_existing=True,
            )
            logger.info("Signal detection job scheduled: %s", signal_cron)

            # Autonomous actions run 1 hour after signal detection
            auto_trigger = _parse_cron(
                "0 10 * * *",
                defaults={
                    "minute": "0",
                    "hour": "10",
                    "day": "*",
                    "month": "*",
                    "day_of_week": "*",
                },
            )
            self.scheduler.add_job(
                self.run_autonomous_actions,
                trigger=auto_trigger,
                id="autonomous_actions",
                replace_existing=True,
            )
            logger.info("Autonomous actions job scheduled")

        # Trending Radar — cross-source topic convergence
        tr_config = self.full_config.get("trending_radar", {})
        if tr_config.get("enabled", True):
            from apscheduler.triggers.interval import IntervalTrigger as _ITrigger

            self.scheduler.add_job(
                self.run_trending_radar,
                trigger=_ITrigger(hours=tr_config.get("interval_hours", 6)),
                id="trending_radar",
                replace_existing=True,
                coalesce=True,
                max_instances=1,
            )
            logger.info(
                "trending_radar.scheduled",
                interval_hours=tr_config.get("interval_hours", 6),
            )

        # Heartbeat — proactive intel-to-goal matching
        hb_config = self.full_config.get("heartbeat", {})
        if hb_config.get("enabled", False):
            from apscheduler.triggers.interval import IntervalTrigger

            self.scheduler.add_job(
                self.run_heartbeat,
                trigger=IntervalTrigger(minutes=hb_config.get("interval_minutes", 30)),
                id="heartbeat",
                replace_existing=True,
                coalesce=True,
                max_instances=1,
            )
            logger.info(
                "heartbeat.scheduled",
                interval_minutes=hb_config.get("interval_minutes", 30),
            )

        # Goal-intel matching — always enabled (zero-cost keyword scoring)
        self.scheduler.add_job(
            self.run_goal_intel_matching,
            trigger=_parse_cron("0 */4 * * *"),
            id="goal_intel_matching",
            replace_existing=True,
        )
        logger.info("Goal-intel matching job scheduled: every 4h")

        # Weekly usage summary — always enabled
        self.scheduler.add_job(
            self.run_weekly_summary,
            trigger=_parse_cron("0 8 * * 1"),
            id="weekly_summary",
            replace_existing=True,
        )
        logger.info("Weekly summary job scheduled: Monday 8am")

        self.scheduler.add_listener(self._default_error_handler, EVENT_JOB_ERROR)
        self.scheduler.start()

    def run_goal_intel_matching(self):
        """Match active goals against recent intel. Keyword scoring + optional LLM eval."""
        if not self.journal_storage:
            return
        try:
            from advisor.goals import GoalTracker

            from .goal_intel_match import (
                GoalIntelLLMEvaluator,
                GoalIntelMatcher,
                GoalIntelMatchStore,
            )

            tracker = GoalTracker(self.journal_storage)
            goals = tracker.get_goals(include_inactive=False)
            if not goals:
                return

            store = GoalIntelMatchStore(self.storage.db_path)
            emb = getattr(self, "intel_embedding_mgr", None)
            matcher = GoalIntelMatcher(self.storage, match_store=store, embedding_manager=emb)
            matches = matcher.match_all_goals(goals)

            # Optional LLM refinement — drops false positives, adjusts urgency
            if matches and GoalIntelLLMEvaluator.is_available():
                try:
                    evaluator = GoalIntelLLMEvaluator()
                    matches = evaluator.evaluate(matches)
                except Exception as e:
                    logger.warning("goal_intel_llm_eval.failed", error=str(e))
            store.save_matches(matches)
            store.cleanup_old(30)
        except Exception as e:
            logger.error("goal_intel_matching_failed", error=str(e))

    def run_heartbeat(self):
        """Run heartbeat cycle: filter recent intel -> evaluate -> notify."""
        if not self.journal_storage:
            return
        try:
            from advisor.goals import GoalTracker

            from .heartbeat import HeartbeatPipeline

            tracker = GoalTracker(self.journal_storage)
            goals = tracker.get_goals(include_inactive=False)
            if not goals:
                return

            hb_config = self.full_config.get("heartbeat", {})
            pipeline = HeartbeatPipeline(
                intel_storage=self.storage,
                goals=goals,
                db_path=self.storage.db_path,
                config=hb_config,
            )
            result = pipeline.run()
            logger.info("heartbeat.complete", **result)
        except Exception as e:
            logger.error("heartbeat.failed", error=str(e))

    def run_weekly_summary(self):
        """Generate and write a weekly usage summary to logs dir."""
        try:
            from web.user_store import get_usage_stats
        except ImportError:
            logger.warning("weekly_summary.skip: web.user_store not available")
            return

        try:
            stats = get_usage_stats(days=7)
            lines = [
                f"Weekly Usage Summary ({datetime.now().strftime('%Y-%m-%d')})",
                "=" * 50,
                f"Chat queries: {stats['chat_queries']}",
                f"Avg latency: {stats['avg_latency_ms'] or 'N/A'}ms",
                f"Active users (7d): {stats['active_users_7d']}",
            ]
            for ev, cnt in stats.get("event_counts", {}).items():
                lines.append(f"{ev}: {cnt}")
            if stats.get("scraper_health"):
                lines.append("\nScraper Health:")
                for s in stats["scraper_health"]:
                    lines.append(f"  {s['source']}: {s['runs']} runs, avg {s['avg_items']} items")
            if stats.get("page_views"):
                lines.append("\nPage Views:")
                for p in stats["page_views"]:
                    lines.append(f"  {p['path']}: {p['count']}")

            log_dir = Path(os.environ.get("COACH_HOME", Path.home() / "coach")) / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            (log_dir / "weekly_summary.txt").write_text("\n".join(lines))
            logger.info("weekly_summary.written", path=str(log_dir / "weekly_summary.txt"))
        except Exception as e:
            logger.error("weekly_summary.failed", error=str(e))

    def run_trending_radar(self):
        """Refresh cross-source trending topics snapshot."""
        try:
            from intelligence.trending_radar import TrendingRadar

            tr_config = self.full_config.get("trending_radar", {})
            radar = TrendingRadar(self.storage.db_path)

            # Try to create a cheap LLM for better summarisation
            llm = None
            try:
                from llm import create_cheap_provider

                llm = create_cheap_provider()
            except Exception:
                pass

            snapshot = radar.refresh(
                llm=llm,
                days=tr_config.get("days", 7),
                min_sources=tr_config.get("min_sources", 2),
                max_topics=tr_config.get("max_topics", 10),
            )
            logger.info(
                "trending_radar.complete",
                topics=len(snapshot.get("topics", [])),
                method=snapshot.get("method", "nlp"),
            )
        except Exception as e:
            logger.error("trending_radar.failed", error=str(e))

    def _add_recommendations_job(self, cron_expr: str):
        """Add weekly recommendations/action brief job."""
        trigger = _parse_cron(
            cron_expr,
            defaults={"minute": "0", "hour": "8", "day": "*", "month": "*", "day_of_week": "0"},
        )
        self.scheduler.add_job(
            self.run_recommendations_now,
            trigger=trigger,
            id="weekly_recommendations",
            replace_existing=True,
        )
        logger.info("Recommendations job scheduled: %s", cron_expr)
