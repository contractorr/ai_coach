"""CLI commands for AI capability horizon model."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from cli.config import load_config

console = Console()


@click.group()
def capabilities():
    """View and manage the AI capability horizon model."""
    pass


@capabilities.command()
def show():
    """Display current capability model as a table."""
    config = load_config()
    db_path = Path(config.get("paths", {}).get("intel_db", "~/coach/intel.db")).expanduser()

    from intelligence.capability_model import CapabilityHorizonModel

    model = CapabilityHorizonModel(db_path)
    if not model.load():
        console.print(
            "[yellow]No capability model found. Run 'coach capabilities refresh' first.[/yellow]"
        )
        return

    table = Table(title="AI Capability Horizon Model")
    table.add_column("Domain", style="cyan")
    table.add_column("Level", justify="right")
    table.add_column("Next Threshold", justify="right")
    table.add_column("Confidence", justify="center")
    table.add_column("Updated", style="dim")

    for d in model.domains:
        # Render level as percentage with bar
        pct = f"{d.current_level * 100:.0f}%"
        bar_len = int(d.current_level * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        level_str = f"{bar} {pct}"

        conf_style = {"high": "green", "medium": "yellow", "low": "red"}.get(d.confidence, "white")

        table.add_row(
            d.name.replace("_", " ").title(),
            level_str,
            f"{d.months_to_next_threshold}mo",
            f"[{conf_style}]{d.confidence}[/{conf_style}]",
            d.last_updated.strftime("%Y-%m-%d"),
        )

    console.print(table)


@capabilities.command()
def refresh():
    """Run all capability scrapers and refresh the model now."""
    config = load_config()
    db_path = Path(config.get("paths", {}).get("intel_db", "~/coach/intel.db")).expanduser()

    from cli.utils import get_intel_storage, get_storage_paths
    from intelligence.capability_model import CapabilityHorizonModel
    from intelligence.scheduler import IntelScheduler

    storage = get_intel_storage(
        config, storage_paths=get_storage_paths(config=config, paths={"intel_db": db_path})
    )
    scheduler = IntelScheduler(
        storage,
        config=config.get("sources", {}),
        full_config=config,
    )

    console.print("[bold]Refreshing capability model...[/bold]")
    result = scheduler.refresh_capability_model()
    console.print(f"Scraped {result['items_scraped']} items, updated {result['domains']} domains.")

    # Show the updated model
    model = CapabilityHorizonModel(db_path)
    if model.load():
        console.print()
        # Re-use show logic inline
        table = Table(title="Updated Capability Model")
        table.add_column("Domain", style="cyan")
        table.add_column("Level", justify="right")
        table.add_column("Months", justify="right")
        table.add_column("Conf", justify="center")

        for d in model.domains:
            pct = f"{d.current_level * 100:.0f}%"
            table.add_row(
                d.name.replace("_", " ").title(),
                pct,
                str(d.months_to_next_threshold),
                d.confidence,
            )
        console.print(table)
