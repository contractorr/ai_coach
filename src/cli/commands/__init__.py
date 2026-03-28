"""CLI command modules."""

from .advisor import ask, goals, opportunities, review, today
from .capabilities import capabilities
from .curriculum import curriculum
from .daemon import daemon
from .database import db
from .eval_cmd import eval_cmd
from .export import export
from .init import init
from .intelligence import (
    brief,
    dedup_backfill,
    intel_export,
    radar,
    scrape,
    scraper_health,
    sources,
    watchlist,
)
from .journal import journal
from .memory import memory
from .profile import profile
from .projects import projects
from .recommend import recommend
from .reflect import reflect
from .research import research
from .threads import threads
from .trends import trends

__all__ = [
    "journal",
    "ask",
    "review",
    "opportunities",
    "goals",
    "scrape",
    "brief",
    "sources",
    "intel_export",
    "radar",
    "scraper_health",
    "watchlist",
    "daemon",
    "curriculum",
    "db",
    "research",
    "recommend",
    "init",
    "trends",
    "reflect",
    "export",
    "profile",
    "projects",
    "capabilities",
    "today",
    "memory",
    "threads",
    "eval_cmd",
    "dedup_backfill",
]


COMMAND_GROUPS = (
    journal,
    daemon,
    curriculum,
    db,
    research,
    recommend,
    export,
    profile,
    projects,
    capabilities,
    memory,
    threads,
)

STANDALONE_COMMANDS = (
    ask,
    review,
    opportunities,
    goals,
    scrape,
    brief,
    sources,
    intel_export,
    init,
    trends,
    reflect,
    today,
    radar,
    scraper_health,
    watchlist,
    eval_cmd,
    dedup_backfill,
)


def register_all(cli):
    """Register all command groups and standalone commands on the CLI root."""
    for command in COMMAND_GROUPS:
        cli.add_command(command)
    for command in STANDALONE_COMMANDS:
        cli.add_command(command)
