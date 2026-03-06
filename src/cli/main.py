"""CLI entry point for AI Coach."""

import sys
from pathlib import Path

import click

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.commands import (
    ask,
    brief,
    capabilities,
    daemon,
    db,
    dedup_backfill,
    eval_cmd,
    export,
    goals,
    init,
    intel_export,
    journal,
    memory,
    opportunities,
    profile,
    projects,
    radar,
    recommend,
    reflect,
    research,
    review,
    scrape,
    scraper_health,
    sources,
    threads,
    today,
    trends,
    watchlist,
)
from cli.config import load_config, setup_logging


@click.group()
@click.version_option(version="0.1.0")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
def cli(verbose: bool):
    """AI Coach - Personal professional advisor."""
    config = load_config()
    if verbose:
        config["logging"] = {"level": "DEBUG", "file_level": "DEBUG"}
    setup_logging(config)


# Register command groups
cli.add_command(journal)
cli.add_command(daemon)
cli.add_command(db)
cli.add_command(research)
cli.add_command(recommend)
cli.add_command(export)
cli.add_command(profile)
cli.add_command(projects)
cli.add_command(capabilities)
cli.add_command(memory)
cli.add_command(threads)

# Register standalone commands
cli.add_command(ask)
cli.add_command(review)
cli.add_command(opportunities)
cli.add_command(goals)
cli.add_command(scrape)
cli.add_command(brief)
cli.add_command(sources)
cli.add_command(intel_export)
cli.add_command(init)
cli.add_command(trends)
cli.add_command(reflect)
cli.add_command(today)
cli.add_command(radar)
cli.add_command(scraper_health)
cli.add_command(watchlist)
cli.add_command(eval_cmd)
cli.add_command(dedup_backfill)


if __name__ == "__main__":
    cli()
