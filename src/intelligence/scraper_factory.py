"""Factory for creating and configuring intelligence scrapers."""

import os

import structlog

from graceful import graceful_context

from .health import RSSFeedHealthTracker
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
    XListScraper,
    YCJobsScraper,
)

logger = structlog.get_logger().bind(source="scraper_factory")


class ScraperFactory:
    """Creates and configures all intelligence scrapers from config."""

    def __init__(self, storage: IntelStorage, sources_config: dict, full_config: dict):
        self.storage = storage
        self.config = sources_config
        self.full_config = full_config

    def create_all(self) -> tuple[list, object | None, RSSFeedHealthTracker]:
        """Create all configured scrapers.

        Returns:
            (scrapers_list, intel_embedding_mgr, feed_health_tracker)
        """
        scrapers: list = []
        feed_health = RSSFeedHealthTracker(self.storage.db_path)
        intel_embedding_mgr = self._create_embedding_mgr()

        enabled = self.config.get("enabled", ["hn_top", "rss_feeds"])
        rss_covered_sources = self._detect_rss_covered_sources()

        # --- Core scrapers ---
        if "hn_top" in enabled and "hn" not in rss_covered_sources:
            scrapers.append(HackerNewsScraper(self.storage))

        config_rss_urls = self._add_rss_scrapers(scrapers, enabled, feed_health)
        self._add_user_rss_scrapers(scrapers, config_rss_urls, feed_health)

        if "custom_blogs" in enabled:
            for url in self.config.get("custom_blogs", []):
                scrapers.append(RSSFeedScraper(self.storage, url, feed_health_tracker=feed_health))

        # --- Optional scrapers ---
        self._add_github_trending(scrapers)
        self._add_arxiv(scrapers, enabled, rss_covered_sources)
        self._add_reddit(scrapers, enabled, rss_covered_sources)
        self._add_events(scrapers)
        self._add_producthunt(scrapers, enabled)
        self._add_yc_jobs(scrapers, enabled)
        self._add_google_patents(scrapers, enabled)
        self._add_ai_capabilities(scrapers, enabled)
        self._add_github_issues(scrapers)
        self._add_capability_horizon_scrapers(scrapers, enabled)
        self._add_indeed(scrapers, enabled)
        self._add_google_trends(scrapers, enabled)
        self._add_crunchbase(scrapers, enabled)
        self._add_x_list(scrapers, enabled)

        # Attach shared embedding manager for semantic dedup + goal matching
        if intel_embedding_mgr:
            for scraper in scrapers:
                scraper.embedding_manager = intel_embedding_mgr

        return scrapers, intel_embedding_mgr, feed_health

    def _create_embedding_mgr(self) -> object | None:
        if not self.config.get("semantic_dedup", False):
            return None
        try:
            from coach_config import get_paths
            from intelligence.embeddings import IntelEmbeddingManager

            paths = get_paths(self.full_config)
            mgr = IntelEmbeddingManager(paths["chroma_dir"])
            logger.info("semantic_dedup.enabled")
            return mgr
        except Exception as e:
            logger.warning("semantic_dedup.init_failed", error=str(e))
            return None

    def _detect_rss_covered_sources(self) -> set[str]:
        if not self.config.get("deduplicate_rss_sources", True):
            return set()
        from intelligence.sources.rss import _detect_source_tag

        covered = set()
        for url in self.config.get("rss_feeds", []):
            tag = _detect_source_tag(url)
            if tag:
                covered.add(tag)
        return covered

    def _add_rss_scrapers(self, scrapers, enabled, feed_health) -> set[str]:
        config_rss_urls: set[str] = set()
        if "rss_feeds" in enabled:
            for url in self.config.get("rss_feeds", []):
                scrapers.append(RSSFeedScraper(self.storage, url, feed_health_tracker=feed_health))
                config_rss_urls.add(url)
        return config_rss_urls

    def _add_user_rss_scrapers(self, scrapers, config_rss_urls, feed_health):
        with graceful_context("graceful.scheduler.rss_merge", log_level="debug"):
            from user_state_store import get_all_user_rss_feeds

            feed_user_map: dict[str, set[str]] = {}
            for feed in get_all_user_rss_feeds():
                feed_user_map.setdefault(feed["url"], set()).add(feed["user_id"])

            for url, user_ids in feed_user_map.items():
                if url not in config_rss_urls:
                    owner = next(iter(user_ids)) if len(user_ids) == 1 else None
                    scrapers.append(
                        RSSFeedScraper(
                            self.storage,
                            url,
                            name=None,
                            feed_health_tracker=feed_health,
                            default_user_id=owner,
                        )
                    )
                    config_rss_urls.add(url)

    def _add_github_trending(self, scrapers):
        gh_config = self.config.get("github_trending", {})
        if gh_config.get("enabled", False):
            scrapers.append(
                GitHubTrendingScraper(
                    self.storage,
                    languages=gh_config.get("languages", ["python"]),
                    timeframe=gh_config.get("timeframe", "daily"),
                )
            )

    def _add_arxiv(self, scrapers, enabled, rss_covered_sources):
        arxiv_config = self.config.get("arxiv", {})
        if (
            "arxiv" in enabled or arxiv_config.get("enabled", False)
        ) and "arxiv" not in rss_covered_sources:
            scrapers.append(
                ArxivScraper(
                    self.storage,
                    categories=arxiv_config.get("categories"),
                    max_results=arxiv_config.get("max_results", 30),
                )
            )

    def _add_reddit(self, scrapers, enabled, rss_covered_sources):
        reddit_config = self.config.get("reddit", {})
        if (
            "reddit" in enabled or reddit_config.get("enabled", False)
        ) and "reddit" not in rss_covered_sources:
            scrapers.append(
                RedditScraper(
                    self.storage,
                    subreddits=reddit_config.get("subreddits"),
                    limit=reddit_config.get("limit", 25),
                    timeframe=reddit_config.get("timeframe", "day"),
                )
            )

    def _add_events(self, scrapers):
        events_config = self.full_config.get("events", {})
        if not events_config.get("enabled", False):
            return
        location = ""
        if events_config.get("location_filter", False):
            with graceful_context("graceful.scheduler.event_location"):
                from profile.storage import ProfileStorage

                profile_path = self.full_config.get("profile", {}).get(
                    "path", "~/coach/profile.yaml"
                )
                ps = ProfileStorage(profile_path)
                p = ps.load()
                if p:
                    location = p.location
        scrapers.append(
            EventScraper(
                self.storage,
                topics=events_config.get("topics"),
                location_filter=location,
                rss_feeds=events_config.get("rss_feeds", []),
            )
        )

    def _add_producthunt(self, scrapers, enabled):
        ph_config = self.config.get("producthunt", {})
        if "producthunt" in enabled or ph_config.get("enabled", False):
            scrapers.append(
                ProductHuntScraper(
                    self.storage,
                    max_items=ph_config.get("max_items", 20),
                )
            )

    def _add_yc_jobs(self, scrapers, enabled):
        yc_config = self.config.get("yc_jobs", {})
        if "yc_jobs" in enabled or yc_config.get("enabled", False):
            scrapers.append(
                YCJobsScraper(
                    self.storage,
                    max_items=yc_config.get("max_items", 30),
                )
            )

    def _add_google_patents(self, scrapers, enabled):
        patents_config = self.config.get("google_patents", {})
        if "google_patents" in enabled or patents_config.get("enabled", False):
            scrapers.append(
                GooglePatentsScraper(
                    self.storage,
                    feeds=patents_config.get("feeds"),
                    max_per_feed=patents_config.get("max_per_feed", 15),
                )
            )

    def _add_ai_capabilities(self, scrapers, enabled):
        ai_cap_config = self.config.get("ai_capabilities", {})
        if "ai_capabilities" in enabled or ai_cap_config.get("enabled", False):
            scrapers.append(
                AICapabilitiesScraper(
                    self.storage,
                    sources=ai_cap_config.get("sources", ["metr", "chatbot_arena", "helm"]),
                    max_items_per_source=ai_cap_config.get("max_items_per_source", 10),
                )
            )

    def _add_github_issues(self, scrapers):
        gh_issues_config = self.full_config.get("projects", {}).get("github_issues", {})
        if not gh_issues_config.get("enabled", False):
            return
        langs = gh_issues_config.get("languages")
        if not langs:
            with graceful_context("graceful.scheduler.gh_issues_langs"):
                from profile.storage import ProfileStorage

                profile_path = self.full_config.get("profile", {}).get(
                    "path", "~/coach/profile.yaml"
                )
                ps = ProfileStorage(profile_path)
                p = ps.load()
                if p:
                    langs = p.languages_frameworks[:5]
        scrapers.append(
            GitHubIssuesScraper(
                self.storage,
                languages=langs or ["python"],
                labels=gh_issues_config.get("labels", ["good-first-issue", "help-wanted"]),
                token=gh_issues_config.get("token"),
            )
        )

    def _add_capability_horizon_scrapers(self, scrapers, enabled):
        cap_config = self.config.get("capability_horizon", {})
        ai_cap_config = self.config.get("ai_capabilities", {})
        if cap_config.get("enabled", False) or (
            "ai_capabilities" in enabled or ai_cap_config.get("enabled", False)
        ):
            scrapers.append(METRScraper(self.storage))
            scrapers.append(EpochAIScraper(self.storage))
            scrapers.append(AIIndexScraper(self.storage))
            scrapers.append(ARCEvalsScraper(self.storage))
            gh_token = self.full_config.get("projects", {}).get("github_issues", {}).get("token")
            scrapers.append(FrontierEvalsGitHubScraper(self.storage, token=gh_token))

    def _add_indeed(self, scrapers, enabled):
        indeed_config = self.config.get("indeed_hiring_lab", {})
        if "indeed_hiring_lab" in enabled or indeed_config.get("enabled", False):
            scrapers.append(
                IndeedHiringLabScraper(
                    self.storage,
                    change_threshold=indeed_config.get("change_threshold", 5.0),
                    max_items=indeed_config.get("max_items", 8),
                )
            )

    def _add_google_trends(self, scrapers, enabled):
        trends_config = self.config.get("google_trends", {})
        if "google_trends" in enabled or trends_config.get("enabled", False):
            scrapers.append(
                GoogleTrendsScraper(
                    self.storage,
                    keywords=trends_config.get("keywords"),
                    spike_threshold=trends_config.get("spike_threshold", 20.0),
                    timeframe=trends_config.get("timeframe", "today 1-m"),
                )
            )

    def _add_crunchbase(self, scrapers, enabled):
        cb_config = self.config.get("crunchbase", {})
        if "crunchbase" in enabled or cb_config.get("enabled", False):
            scrapers.append(
                CrunchbaseScraper(
                    self.storage,
                    api_key=cb_config.get("api_key"),
                    categories=cb_config.get("categories"),
                    days_back=cb_config.get("days_back", 7),
                    max_items=cb_config.get("max_items", 20),
                )
            )

    def _add_x_list(self, scrapers, enabled):
        x_list_config = self.config.get("x_list", {})
        if "x_list" in enabled or x_list_config.get("enabled", False):
            bearer = x_list_config.get("bearer_token") or os.environ.get("X_BEARER_TOKEN")
            list_id = x_list_config.get("list_id")
            if bearer and list_id:
                scrapers.append(
                    XListScraper(
                        self.storage,
                        bearer_token=bearer,
                        list_id=list_id,
                        max_tweets=x_list_config.get("max_tweets", 100),
                    )
                )
