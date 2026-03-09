"""Shared briefing data assembly used by both /api/briefing and /api/greeting."""

from datetime import datetime, timedelta

import structlog

from advisor.assumptions import refresh_active_assumptions
from advisor.outcomes import OutcomeHarvester
from storage_access import (
    create_goal_intel_match_store,
    create_profile_storage,
    create_recommendation_storage,
)
from web.deps import (
    get_assumption_store,
    get_company_movement_store,
    get_dossier_escalation_store,
    get_hiring_signal_store,
    get_outcome_store,
    get_regulatory_alert_store,
    get_user_paths,
    get_watchlist_store,
)

logger = structlog.get_logger()


def assemble_briefing_data(user_id: str) -> dict:
    """Assemble core briefing data: profile, stale goals, all goals, recs, intel matches.

    Returns dict with keys: name, stale_goals, all_goals, recommendations, goal_intel_matches,
    company_movements, hiring_signals, regulatory_alerts, dossier_escalations, assumptions.
    Each key is always present (empty list / empty string as default).
    """
    paths = get_user_paths(user_id)
    data: dict = {
        "name": "",
        "stale_goals": [],
        "all_goals": [],
        "recommendations": [],
        "goal_intel_matches": [],
        "company_movements": [],
        "hiring_signals": [],
        "regulatory_alerts": [],
        "dossier_escalations": [],
        "assumptions": [],
    }

    def _candidate_signals() -> list[dict]:
        signals = []
        try:
            signals.extend(
                get_company_movement_store().get_since(
                    datetime.now() - timedelta(days=30), limit=100
                )
            )
        except Exception:
            pass
        try:
            signals.extend(get_hiring_signal_store().get_recent(limit=100))
        except Exception:
            pass
        try:
            signals.extend(
                get_regulatory_alert_store().get_recent(
                    datetime.now() - timedelta(days=60), limit=100
                )
            )
        except Exception:
            pass
        return signals

    def _serialize_company_movement(item: dict) -> dict:
        return {
            "id": item.get("id", 0),
            "company_key": item.get("company_key") or "",
            "company_label": item.get("company_label") or item.get("company_key") or "",
            "movement_type": item.get("movement_type") or "product",
            "title": item.get("title") or "Company movement detected",
            "summary": item.get("summary") or "",
            "significance": float(item.get("significance") or 0.0),
            "source_url": item.get("source_url") or "",
            "source_family": item.get("source_family") or "",
            "observed_at": item.get("observed_at") or "",
            "metadata": item.get("metadata") or {},
        }

    def _serialize_hiring_signal(item: dict) -> dict:
        return {
            "id": item.get("id", 0),
            "entity_key": item.get("entity_key") or "",
            "entity_label": item.get("entity_label") or item.get("entity_key") or "",
            "signal_type": item.get("signal_type") or "jobs",
            "title": item.get("title") or "Hiring signal detected",
            "summary": item.get("summary") or "",
            "strength": float(item.get("strength") or 0.0),
            "source_url": item.get("source_url") or "",
            "observed_at": item.get("observed_at") or "",
            "metadata": item.get("metadata") or {},
        }

    def _serialize_regulatory_alert(item: dict) -> dict:
        return {
            "id": item.get("id", 0),
            "target_key": item.get("target_key") or "",
            "title": item.get("title") or "Regulatory alert",
            "summary": item.get("summary") or "",
            "source_family": item.get("source_family") or "",
            "change_type": item.get("change_type") or "guidance",
            "urgency": item.get("urgency") or "low",
            "relevance": float(item.get("relevance") or 0.0),
            "effective_date": item.get("effective_date"),
            "source_url": item.get("source_url") or "",
            "observed_at": item.get("observed_at") or "",
            "metadata": item.get("metadata") or {},
        }

    # Profile name
    try:
        prof = create_profile_storage(paths).load()
        if prof:
            data["name"] = getattr(prof, "name", None) or getattr(prof, "current_role", "")
    except Exception:
        pass

    # Goals
    try:
        from advisor.goals import GoalTracker
        from journal.storage import JournalStorage

        storage = JournalStorage(paths["journal_dir"])
        tracker = GoalTracker(storage)
        raw_stale = tracker.get_stale_goals()
        data["stale_goals"] = [
            {
                "path": str(g["path"]),
                "title": g["title"],
                "status": g["status"],
                "days_since_check": g.get("days_since_check") or 0,
            }
            for g in raw_stale
        ]
        raw_all = tracker.get_goals(include_inactive=False)
        data["all_goals"] = [
            {
                "path": str(g["path"]),
                "title": g["title"],
                "status": g["status"],
                "days_since_check": g.get("days_since_check") or 0,
            }
            for g in raw_all
        ]
    except Exception as e:
        logger.warning("briefing_data.goals_error", error=str(e))

    # Recommendations
    try:
        rec_dir = paths.get("recommendations_dir")
        if rec_dir:
            rec_storage = create_recommendation_storage(paths)
            harvester = OutcomeHarvester(get_outcome_store(user_id), rec_storage)
            recs = rec_storage.get_top_by_score(limit=5)
            for r in recs:
                meta = r.metadata or {}
                critic = None
                if any(meta.get(k) for k in ("confidence", "critic_challenge", "missing_context")):
                    critic = {
                        "confidence": meta.get("confidence", "Medium"),
                        "confidence_rationale": meta.get("confidence_rationale", ""),
                        "critic_challenge": meta.get("critic_challenge", ""),
                        "missing_context": meta.get("missing_context", ""),
                        "alternative": meta.get("alternative"),
                        "intel_contradictions": meta.get("intel_contradictions"),
                    }
                harvested_outcome = None
                try:
                    harvested_outcome = harvester.evaluate_recommendation(
                        {"id": r.id or "", "metadata": meta}
                    )
                except Exception as e:
                    logger.warning(
                        "briefing_data.recommendation_outcome_error",
                        error=str(e),
                        recommendation_id=r.id,
                    )
                data["recommendations"].append(
                    {
                        "id": r.id or "",
                        "category": r.category,
                        "title": r.title,
                        "description": r.description[:200] if r.description else "",
                        "score": r.score,
                        "status": r.status,
                        "reasoning_trace": meta.get("reasoning_trace"),
                        "critic": critic,
                        "harvested_outcome": harvested_outcome,
                    }
                )
    except Exception as e:
        logger.warning("briefing_data.recommendations_error", error=str(e))

    # Goal-intel matches
    try:
        match_store = create_goal_intel_match_store(paths)
        goal_paths = [g["path"] for g in data["all_goals"]]
        if goal_paths:
            data["goal_intel_matches"] = match_store.get_matches(goal_paths=goal_paths, limit=20)
    except Exception as e:
        logger.warning("briefing_data.goal_intel_matches_error", error=str(e))

    # Pipeline-specific watchlist intel
    try:
        from intelligence.company_watch import WatchedCompanyResolver
        from intelligence.regulatory import RegulatoryWatchResolver

        watchlist_items = get_watchlist_store(user_id).list_items()

        companies = WatchedCompanyResolver().from_watchlist_items(watchlist_items)
        company_keys = {item["company_key"] for item in companies if item.get("company_key")}
        if company_keys:
            company_rows = [
                item
                for item in get_company_movement_store().get_since(
                    datetime.now() - timedelta(days=30), limit=40
                )
                if item.get("company_key") in company_keys
            ]
            data["company_movements"] = [
                _serialize_company_movement(item) for item in company_rows[:5]
            ]

            hiring_rows = [
                item
                for item in get_hiring_signal_store().get_recent(limit=40)
                if item.get("entity_key") in company_keys
            ]
            data["hiring_signals"] = [_serialize_hiring_signal(item) for item in hiring_rows[:5]]

        targets = RegulatoryWatchResolver().from_watchlist_items(watchlist_items)
        target_keys = {item["target_key"] for item in targets if item.get("target_key")}
        if target_keys:
            regulatory_rows = [
                item
                for item in get_regulatory_alert_store().get_recent(
                    datetime.now() - timedelta(days=60), limit=40
                )
                if item.get("target_key") in target_keys
            ]
            data["regulatory_alerts"] = [
                _serialize_regulatory_alert(item) for item in regulatory_rows[:5]
            ]
    except Exception as e:
        logger.warning("briefing_data.pipeline_intel_error", error=str(e))

    # Dossier escalations (persisted active rows only; fresh scoring remains route-driven)
    try:
        data["dossier_escalations"] = get_dossier_escalation_store(user_id).list_active(limit=5)
    except Exception as e:
        logger.warning("briefing_data.dossier_escalations_error", error=str(e))

    # Assumptions
    try:
        refreshed_assumptions = refresh_active_assumptions(
            get_assumption_store(user_id), _candidate_signals(), limit=20
        )
        interesting_assumptions = [
            item
            for item in refreshed_assumptions
            if item.get("status") in {"suggested", "confirmed", "invalidated"}
            or item.get("latest_evidence_summary")
        ]
        data["assumptions"] = [
            {
                "id": item["id"],
                "title": item.get("statement") or "Assumption update",
                "detail": item.get("latest_evidence_summary")
                or f"Status: {item.get('status', 'active')}",
                "status": item.get("status"),
                "updated_at": item.get("updated_at"),
            }
            for item in interesting_assumptions[:5]
        ]
    except Exception as e:
        logger.warning("briefing_data.assumptions_error", error=str(e))

    return data
