"""Unified pipeline framework for watchlist-driven intelligence processing."""

from dataclasses import dataclass, field
from typing import Any, Callable

import structlog

from .scraper import IntelStorage

logger = structlog.get_logger().bind(source="watchlist_pipeline")


@dataclass
class WatchlistPipelineConfig:
    """Describes a single watchlist pipeline variant."""

    name: str  # e.g. "company_movement"
    config_key: str  # key in full_config
    entity_key_field: str  # "company_key" | "entity_key" | "target_key"
    default_lookback_days: int
    default_limit_per_entity: int
    empty_result: dict = field(default_factory=dict)


class WatchlistPipeline:
    """Runs a watchlist-driven pipeline: load → resolve → dedup → fetch → process → persist."""

    def __init__(
        self,
        storage: IntelStorage,
        full_config: dict,
        pipeline_config: WatchlistPipelineConfig,
        resolver: Callable[[list[dict]], list[dict]],
        processor: Callable[[list[dict], list[dict], dict], list[dict]],
        store_factory: Callable[[Any], Any],
        result_builder: Callable[[int, int, int], dict] | None = None,
    ):
        self.storage = storage
        self.full_config = full_config
        self.cfg = pipeline_config
        self.resolver = resolver
        self.processor = processor
        self.store_factory = store_factory
        self.result_builder = result_builder

    def run(self) -> dict:
        from .watchlist import list_all_watchlist_items

        pipeline_conf = self.full_config.get(self.cfg.config_key, {})
        watchlist_items = list_all_watchlist_items()
        entities = self.resolver(watchlist_items)

        # Dedup by priority
        by_key: dict[str, dict] = {}
        for entity in entities:
            key = entity.get(self.cfg.entity_key_field) or ""
            if key and (
                key not in by_key or entity.get("priority", 0) > by_key[key].get("priority", 0)
            ):
                by_key[key] = entity
        entities = list(by_key.values())

        if not entities:
            return dict(self.cfg.empty_result)

        lookback_days = int(
            pipeline_conf.get("lookback_days", self.cfg.default_lookback_days)
            or self.cfg.default_lookback_days
        )
        recent_items = self.storage.get_recent(
            days=lookback_days,
            limit=max(self.cfg.default_limit_per_entity, len(entities) * 25),
            include_duplicates=True,
        )

        results = self.processor(entities, recent_items, pipeline_conf)
        store = self.store_factory(self.storage.db_path)
        saved = store.save_many(results)

        logger.info(
            f"{self.cfg.name}.complete",
            entities=len(entities),
            detected=len(results),
            saved=saved,
        )

        if self.result_builder:
            return self.result_builder(len(entities), len(results), saved)
        return {"entities": len(entities), "detected": len(results), "saved": saved}


# --- Factory functions for the 3 pipelines ---


def create_company_movement_pipeline(storage: IntelStorage, full_config: dict) -> WatchlistPipeline:
    from .company_watch import (
        CompanyMovementCollector,
        CompanyMovementStore,
        WatchedCompanyResolver,
    )

    def resolver(watchlist_items):
        return WatchedCompanyResolver().from_watchlist_items(watchlist_items)

    def processor(entities, recent_items, pipeline_conf):
        min_significance = float(pipeline_conf.get("min_significance", 0.45) or 0.45)
        collector = CompanyMovementCollector()
        return [
            event
            for event in collector.collect(entities, recent_items)
            if float(event.get("significance") or 0.0) >= min_significance
        ]

    def result_builder(n_entities, n_detected, n_saved):
        return {
            "watched_companies": n_entities,
            "events_detected": n_detected,
            "saved": n_saved,
        }

    return WatchlistPipeline(
        storage=storage,
        full_config=full_config,
        pipeline_config=WatchlistPipelineConfig(
            name="company_movement",
            config_key="company_movement",
            entity_key_field="company_key",
            default_lookback_days=14,
            default_limit_per_entity=200,
            empty_result={"watched_companies": 0, "events_detected": 0, "saved": 0},
        ),
        resolver=resolver,
        processor=processor,
        store_factory=CompanyMovementStore,
        result_builder=result_builder,
    )


def create_hiring_pipeline(storage: IntelStorage, full_config: dict) -> WatchlistPipeline:
    from .company_watch import WatchedCompanyResolver
    from .hiring_signals import HiringSignalAnalyzer, HiringSignalStore

    def resolver(watchlist_items):
        return WatchedCompanyResolver().from_watchlist_items(watchlist_items)

    def processor(entities, recent_items, _pipeline_conf):
        return HiringSignalAnalyzer().analyze_mentions(entities, recent_items)

    def result_builder(n_entities, n_detected, n_saved):
        return {
            "watched_entities": n_entities,
            "signals_detected": n_detected,
            "saved": n_saved,
        }

    return WatchlistPipeline(
        storage=storage,
        full_config=full_config,
        pipeline_config=WatchlistPipelineConfig(
            name="hiring_pipeline",
            config_key="hiring",
            entity_key_field="company_key",
            default_lookback_days=14,
            default_limit_per_entity=200,
            empty_result={"watched_entities": 0, "signals_detected": 0, "saved": 0},
        ),
        resolver=resolver,
        processor=processor,
        store_factory=HiringSignalStore,
        result_builder=result_builder,
    )


def create_regulatory_pipeline(storage: IntelStorage, full_config: dict) -> WatchlistPipeline:
    from .regulatory import RegulatoryAlertStore, RegulatoryClassifier, RegulatoryWatchResolver

    def resolver(watchlist_items):
        return RegulatoryWatchResolver().from_watchlist_items(watchlist_items)

    def processor(entities, recent_items, pipeline_conf):
        min_relevance = float(pipeline_conf.get("min_relevance", 0.5) or 0.5)
        classifier = RegulatoryClassifier()
        alerts: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for target in entities:
            for intel_item in recent_items:
                alert = classifier.classify(intel_item, target)
                if not alert or float(alert.get("relevance") or 0.0) < min_relevance:
                    continue
                dedupe_key = (alert.get("target_key") or "", alert.get("source_url") or "")
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                alerts.append(alert)
        return alerts

    def result_builder(n_entities, n_detected, n_saved):
        return {"targets": n_entities, "alerts_detected": n_detected, "saved": n_saved}

    return WatchlistPipeline(
        storage=storage,
        full_config=full_config,
        pipeline_config=WatchlistPipelineConfig(
            name="regulatory_pipeline",
            config_key="regulatory",
            entity_key_field="target_key",
            default_lookback_days=30,
            default_limit_per_entity=250,
            empty_result={"targets": 0, "alerts_detected": 0, "saved": 0},
        ),
        resolver=resolver,
        processor=processor,
        store_factory=RegulatoryAlertStore,
        result_builder=result_builder,
    )
