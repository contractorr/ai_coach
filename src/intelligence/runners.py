"""Standalone runner functions and classes extracted from IntelScheduler."""

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import structlog

from storage_paths import get_coach_home

from .scraper import IntelStorage

logger = structlog.get_logger().bind(source="runners")


@dataclass
class RunnerContext:
    """Shared context for runner functions."""

    storage: IntelStorage
    full_config: dict = field(default_factory=dict)
    journal_storage: Any = None
    embeddings: Any = None
    intel_embedding_mgr: Any = None


# ---------------------------------------------------------------------------
# ResearchRunner + RecommendationRunner (classes, moved verbatim)
# ---------------------------------------------------------------------------


class ResearchRunner:
    """Handles deep research agent initialization and execution."""

    def __init__(self, storage: IntelStorage, journal_storage, embeddings, config: dict):
        self.storage = storage
        self.journal_storage = journal_storage
        self.embeddings = embeddings
        self.config = config

    def _init_agent(self):
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

    def run(self, topic: Optional[str] = None, dossier_id: Optional[str] = None) -> list[dict]:
        agent = self._init_agent()
        if not agent:
            logger.warning("Research agent not available")
            return []
        try:
            return agent.run(specific_topic=topic, dossier_id=dossier_id)
        finally:
            agent.close()

    def list_dossiers(self, include_archived: bool = False, limit: int = 50) -> list[dict]:
        agent = self._init_agent()
        if not agent:
            return []
        try:
            return agent.list_dossiers(include_archived=include_archived, limit=limit)
        finally:
            agent.close()

    def create_dossier(self, **kwargs) -> dict | None:
        agent = self._init_agent()
        if not agent:
            return None
        try:
            return agent.create_dossier(**kwargs)
        finally:
            agent.close()

    def get_dossier(self, dossier_id: str) -> dict | None:
        agent = self._init_agent()
        if not agent:
            return None
        try:
            return agent.get_dossier(dossier_id)
        finally:
            agent.close()

    def get_topics(self) -> list[dict]:
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
            brief_saved = False
            if "journal" in delivery.get("methods", ["journal"]):
                advisor.generate_action_brief(
                    rec_db,
                    journal_storage=self.journal_storage,
                    save=True,
                )
                brief_saved = True
                logger.info("Action brief saved to journal")

            return {"recommendations": len(recs), "brief_saved": brief_saved}

        except Exception as e:
            logger.error("Failed to generate recommendations: %s", e)
            return {"error": str(e)}


# ---------------------------------------------------------------------------
# Standalone runner functions
# ---------------------------------------------------------------------------


def run_signal_detection(ctx: RunnerContext) -> list:
    if not ctx.journal_storage:
        logger.warning("Signal detection requires journal_storage")
        return []
    try:
        from advisor.signals import SignalDetector

        db_path = ctx.storage.db_path
        repo_store = None
        gh_config = ctx.full_config.get("github_monitoring", {})
        if gh_config.get("enabled", False):
            try:
                from intelligence.github_repo_store import GitHubRepoStore

                repo_store = GitHubRepoStore(db_path)
            except Exception:
                pass
        detector = SignalDetector(
            ctx.journal_storage, db_path, ctx.full_config, repo_store=repo_store
        )
        signals = detector.detect_all()
        logger.info("signal_detection_complete", count=len(signals))
        return signals
    except Exception as e:
        logger.error("signal_detection_failed", error=str(e))
        return []


def run_autonomous_actions(ctx: RunnerContext) -> list:
    if not ctx.journal_storage:
        logger.warning("Autonomous actions require journal_storage")
        return []
    try:
        from advisor.autonomous import AutonomousActionEngine
        from advisor.signals import Signal, SignalStore, SignalType

        db_path = ctx.storage.db_path
        store = SignalStore(db_path)
        active_signals = store.get_active(limit=20)

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
            ctx.journal_storage, db_path, ctx.full_config, ctx.embeddings
        )
        results = engine.process_signals(signals)
        logger.info("autonomous_actions_complete", count=len(results))
        return results
    except Exception as e:
        logger.error("autonomous_actions_failed", error=str(e))
        return []


def refresh_capability_model(ctx: RunnerContext) -> dict:
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
            METRScraper(ctx.storage),
            EpochAIScraper(ctx.storage),
            AIIndexScraper(ctx.storage),
            ARCEvalsScraper(ctx.storage),
            FrontierEvalsGitHubScraper(ctx.storage),
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

    model = CapabilityHorizonModel(ctx.storage.db_path)
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


def run_github_repo_poll(ctx: RunnerContext) -> dict:
    gh_config = ctx.full_config.get("github_monitoring", {})
    if not gh_config.get("enabled", False):
        return {"status": "disabled"}

    try:
        from intelligence.github_repo_poller import GitHubRepoPoller
        from intelligence.github_repo_store import GitHubRepoStore
        from intelligence.github_repos import GitHubRepoClient

        store = GitHubRepoStore(ctx.storage.db_path)
        user_ids = store.get_all_user_ids_with_repos()
        if not user_ids:
            return {"status": "no_repos"}

        total_snapshots = 0
        for user_id in user_ids:
            token = None
            try:
                from user_state_store import get_user_secret

                fernet_key = os.environ.get("SECRET_KEY", "")
                if fernet_key:
                    token = get_user_secret(user_id, "github_pat", fernet_key)
                    if not token:
                        token = get_user_secret(user_id, "github_token", fernet_key)
            except Exception:
                pass

            client = GitHubRepoClient(
                token=token,
                base_url=gh_config.get("api_base_url", "https://api.github.com"),
                timeout=gh_config.get("request_timeout_s", 15),
            )
            poller = GitHubRepoPoller(client, store)
            try:
                snapshots = asyncio.run(poller.poll_user_repos(user_id))
                total_snapshots += len(snapshots)
            except Exception as e:
                logger.warning(
                    "github_repo_poll.user_failed",
                    user_id=user_id,
                    error=str(e),
                )
            finally:
                asyncio.run(client.close())

        retention = gh_config.get("snapshot_retention_days", 90)
        pruned = store.prune_snapshots(retention)
        logger.info(
            "github_repo_poll.complete",
            users=len(user_ids),
            snapshots=total_snapshots,
            pruned=pruned,
        )
        return {"users": len(user_ids), "snapshots": total_snapshots, "pruned": pruned}
    except Exception as e:
        logger.error("github_repo_poll.failed", error=str(e))
        return {"error": str(e)}


def run_goal_intel_matching(ctx: RunnerContext) -> None:
    if not ctx.journal_storage:
        return
    try:
        from advisor.goals import GoalTracker
        from intelligence.goal_intel_match import (
            GoalIntelLLMEvaluator,
            GoalIntelMatcher,
            GoalIntelMatchStore,
        )

        tracker = GoalTracker(ctx.journal_storage)
        goals = tracker.get_goals(include_inactive=False)
        if not goals:
            return

        store = GoalIntelMatchStore(ctx.storage.db_path)
        matcher = GoalIntelMatcher(
            ctx.storage, match_store=store, embedding_manager=ctx.intel_embedding_mgr
        )
        matches = matcher.match_all_goals(goals)

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


def run_heartbeat(ctx: RunnerContext) -> None:
    if not ctx.journal_storage:
        return
    try:
        from advisor.goals import GoalTracker
        from intelligence.heartbeat import HeartbeatPipeline

        tracker = GoalTracker(ctx.journal_storage)
        goals = tracker.get_goals(include_inactive=False)
        if not goals:
            return

        hb_config = ctx.full_config.get("heartbeat", {})
        pipeline = HeartbeatPipeline(
            intel_storage=ctx.storage,
            goals=goals,
            db_path=ctx.storage.db_path,
            config=hb_config,
        )
        result = pipeline.run()
        logger.info("heartbeat.complete", **result)
    except Exception as e:
        logger.error("heartbeat.failed", error=str(e))


def run_trending_radar(ctx: RunnerContext) -> None:
    try:
        from intelligence.trending_radar import TrendingRadar

        tr_config = ctx.full_config.get("trending_radar", {})
        radar = TrendingRadar(ctx.storage.db_path)

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


def run_weekly_summary(ctx: RunnerContext) -> None:
    try:
        from user_state_store import get_usage_stats
    except ImportError:
        logger.warning("weekly_summary.skip: user_state_store not available")
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

        log_dir = get_coach_home() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "weekly_summary.txt").write_text("\n".join(lines))
        logger.info("weekly_summary.written", path=str(log_dir / "weekly_summary.txt"))
    except Exception as e:
        logger.error("weekly_summary.failed", error=str(e))


def run_memory_consolidation(ctx: RunnerContext) -> dict:
    memory_config = ctx.full_config.get("memory", {})
    consolidation_config = memory_config.get("consolidation", {})
    if not consolidation_config.get("enabled", True):
        return {"status": "disabled"}

    try:
        from memory.consolidator import ObservationConsolidator
        from memory.store import FactStore

        paths_config = ctx.full_config.get("paths", {})
        coach_home = get_coach_home()
        db_path = Path(paths_config.get("memory_db", str(coach_home / "memory.db"))).expanduser()
        if not db_path.exists():
            return {"status": "no_db"}

        store = FactStore(db_path, chroma_dir=None)
        consolidator = ObservationConsolidator(
            store,
            min_facts_per_group=consolidation_config.get("min_facts_per_group", 2),
        )
        observations = consolidator.consolidate_all()
        logger.info("memory_consolidation.complete", observations=len(observations))
        return {"observations": len(observations)}
    except Exception as e:
        logger.error("memory_consolidation.failed", error=str(e))
        return {"error": str(e)}
