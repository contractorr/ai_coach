"""Declarative job specifications for the intelligence scheduler."""

from dataclasses import dataclass, field
from typing import Any, Callable

import structlog
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = structlog.get_logger().bind(source="job_registry")


def _parse_cron(expr: str, defaults: dict | None = None) -> CronTrigger:
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


@dataclass
class JobSpec:
    """Declarative description of a scheduled job."""

    id: str
    func: Callable
    trigger_type: str  # "cron" | "interval"
    trigger_value: str | dict = ""
    trigger_defaults: dict = field(default_factory=dict)
    enabled_check: Callable[[dict, dict], bool] | None = None
    coalesce: bool = False
    max_instances: int = 1
    log_message: str = ""


def build_job_specs(scheduler_instance: Any, scrape_cron: str, research_cron: str) -> list[JobSpec]:
    """Build all job specs from scheduler instance and config."""
    s = scheduler_instance
    sources_config = s.config
    full_config = s.full_config
    specs: list[JobSpec] = []

    # 1) Scraping
    specs.append(
        JobSpec(
            id="intel_gather",
            func=s.run_now,
            trigger_type="cron",
            trigger_value=scrape_cron,
        )
    )

    # 2) Capability model refresh
    cap_config = sources_config.get("capability_horizon", {})
    ai_cap_config = sources_config.get("ai_capabilities", {})
    enabled_sources = sources_config.get("enabled", [])
    if (
        cap_config.get("enabled", False)
        or "ai_capabilities" in enabled_sources
        or ai_cap_config.get("enabled", False)
    ):
        specs.append(
            JobSpec(
                id="refresh_capability_model",
                func=s.refresh_capability_model,
                trigger_type="cron",
                trigger_value=scrape_cron,
                log_message=f"Capability model refresh job scheduled: {scrape_cron}",
            )
        )

    # 3) Research
    research_config = full_config.get("research", {})
    if research_config.get("enabled", False):
        specs.append(
            JobSpec(
                id="deep_research",
                func=s.run_research_now,
                trigger_type="cron",
                trigger_value=research_cron,
                trigger_defaults={
                    "minute": "0",
                    "hour": "21",
                    "day": "*",
                    "month": "*",
                    "day_of_week": "0",
                },
                log_message=f"Research job scheduled: {research_cron}",
            )
        )

    # 4) Recommendations
    rec_config = full_config.get("recommendations", {})
    if rec_config.get("enabled", False):
        rec_cron = rec_config.get("delivery", {}).get("schedule", "0 8 * * 0")
        specs.append(
            JobSpec(
                id="weekly_recommendations",
                func=s.run_recommendations_now,
                trigger_type="cron",
                trigger_value=rec_cron,
                trigger_defaults={
                    "minute": "0",
                    "hour": "8",
                    "day": "*",
                    "month": "*",
                    "day_of_week": "0",
                },
                log_message=f"Recommendations job scheduled: {rec_cron}",
            )
        )

    # 5) Company movement pipeline
    company_config = full_config.get("company_movement", {})
    if company_config.get("enabled", False):
        cron = company_config.get("run_cron", "0 */6 * * *")
        specs.append(
            JobSpec(
                id="company_movement_pipeline",
                func=s.run_company_movement_pipeline,
                trigger_type="cron",
                trigger_value=cron,
                log_message=f"company_movement.scheduled cron={cron}",
            )
        )

    # 6) Hiring pipeline
    hiring_config = full_config.get("hiring", {})
    if hiring_config.get("enabled", False):
        cron = hiring_config.get("run_cron", "0 */12 * * *")
        specs.append(
            JobSpec(
                id="hiring_activity_pipeline",
                func=s.run_hiring_activity_pipeline,
                trigger_type="cron",
                trigger_value=cron,
                log_message=f"hiring_pipeline.scheduled cron={cron}",
            )
        )

    # 7) Regulatory pipeline
    reg_config = full_config.get("regulatory", {})
    if reg_config.get("enabled", False):
        cron = reg_config.get("run_cron", "0 */12 * * *")
        specs.append(
            JobSpec(
                id="regulatory_pipeline",
                func=s.run_regulatory_pipeline,
                trigger_type="cron",
                trigger_value=cron,
                log_message=f"regulatory_pipeline.scheduled cron={cron}",
            )
        )

    # 8) Entity extraction
    entity_config = full_config.get("entity_extraction", {})
    if entity_config.get("enabled", True) is not False:
        specs.append(
            JobSpec(
                id="entity_extraction",
                func=s.run_entity_extraction,
                trigger_type="interval",
                trigger_value={"minutes": entity_config.get("schedule_minutes", 30)},
                coalesce=True,
                log_message=f"entity_extraction.scheduled interval_minutes={entity_config.get('schedule_minutes', 30)}",
            )
        )

    # 9) Memory consolidation
    memory_config = full_config.get("memory", {})
    consolidation_config = memory_config.get("consolidation", {})
    if consolidation_config.get("enabled", True):
        cron = consolidation_config.get("run_cron", "0 3 * * *")
        specs.append(
            JobSpec(
                id="memory_consolidation",
                func=s.run_memory_consolidation,
                trigger_type="cron",
                trigger_value=cron,
                coalesce=True,
                log_message=f"memory_consolidation.scheduled cron={cron}",
            )
        )

    # 10) Signal detection + autonomous actions
    agent_config = full_config.get("agent", {})
    if agent_config.get("enabled", False):
        signal_cron = agent_config.get("signals", {}).get("schedule", "0 9 * * *")
        specs.append(
            JobSpec(
                id="signal_detection",
                func=s.run_signal_detection,
                trigger_type="cron",
                trigger_value=signal_cron,
                log_message=f"Signal detection job scheduled: {signal_cron}",
            )
        )
        specs.append(
            JobSpec(
                id="autonomous_actions",
                func=s.run_autonomous_actions,
                trigger_type="cron",
                trigger_value="0 10 * * *",
                trigger_defaults={
                    "minute": "0",
                    "hour": "10",
                    "day": "*",
                    "month": "*",
                    "day_of_week": "*",
                },
                log_message="Autonomous actions job scheduled",
            )
        )

    # 11) Trending radar
    tr_config = full_config.get("trending_radar", {})
    if tr_config.get("enabled", True):
        specs.append(
            JobSpec(
                id="trending_radar",
                func=s.run_trending_radar,
                trigger_type="interval",
                trigger_value={"hours": tr_config.get("interval_hours", 6)},
                coalesce=True,
                log_message=f"trending_radar.scheduled interval_hours={tr_config.get('interval_hours', 6)}",
            )
        )

    # 12) Heartbeat
    hb_config = full_config.get("heartbeat", {})
    if hb_config.get("enabled", True):
        specs.append(
            JobSpec(
                id="heartbeat",
                func=s.run_heartbeat,
                trigger_type="interval",
                trigger_value={"minutes": hb_config.get("interval_minutes", 30)},
                coalesce=True,
                log_message=f"heartbeat.scheduled interval_minutes={hb_config.get('interval_minutes', 30)}",
            )
        )

    # 13) Goal-intel matching (always enabled)
    specs.append(
        JobSpec(
            id="goal_intel_matching",
            func=s.run_goal_intel_matching,
            trigger_type="cron",
            trigger_value="0 */4 * * *",
            log_message="Goal-intel matching job scheduled: every 4h",
        )
    )

    # 14) Weekly summary (always enabled)
    specs.append(
        JobSpec(
            id="weekly_summary",
            func=s.run_weekly_summary,
            trigger_type="cron",
            trigger_value="0 8 * * 1",
            log_message="Weekly summary job scheduled: Monday 8am",
        )
    )

    # 15) GitHub repo monitoring
    gh_mon_config = full_config.get("github_monitoring", {})
    if gh_mon_config.get("enabled", False):
        gh_cron = gh_mon_config.get("poll_cron", "0 */4 * * *")
        specs.append(
            JobSpec(
                id="github_repo_poll",
                func=s.run_github_repo_poll,
                trigger_type="cron",
                trigger_value=gh_cron,
                log_message=f"github_repo_poll.scheduled cron={gh_cron}",
            )
        )

    return specs


def register_jobs(bg_scheduler, specs: list[JobSpec]) -> None:
    """Register all job specs on an APScheduler BackgroundScheduler."""
    for spec in specs:
        if spec.trigger_type == "cron":
            trigger = _parse_cron(
                spec.trigger_value,
                defaults=spec.trigger_defaults if spec.trigger_defaults else None,
            )
        elif spec.trigger_type == "interval":
            trigger = IntervalTrigger(**spec.trigger_value)
        else:
            raise ValueError(f"Unknown trigger type: {spec.trigger_type}")

        kwargs: dict = {
            "trigger": trigger,
            "id": spec.id,
            "replace_existing": True,
        }
        if spec.coalesce:
            kwargs["coalesce"] = True
            kwargs["max_instances"] = spec.max_instances
            kwargs["misfire_grace_time"] = 300

        bg_scheduler.add_job(spec.func, **kwargs)

        if spec.log_message:
            logger.info(spec.log_message)
