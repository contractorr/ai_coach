"""Thread detection CLI commands."""

import asyncio

import click
from rich.console import Console
from rich.table import Table

from cli.utils import get_components, get_thread_store

console = Console()


@click.group()
def threads():
    """Journal recurrence detection ? view and manage topic threads."""
    pass


@threads.command("list")
@click.option("-n", "--limit", default=10, help="Max threads to show")
def threads_list(limit: int):
    """List active threads with entry count and timespan."""
    c = get_components(skip_advisor=True)
    store = get_thread_store(c["config"], c.get("storage_paths"))

    loop = asyncio.get_event_loop()
    active = loop.run_until_complete(store.get_active_threads(min_entries=2))

    if not active:
        console.print("[yellow]No active threads found.[/]")
        return

    table = Table(show_header=True)
    table.add_column("Label", max_width=50)
    table.add_column("Entries", justify="right")
    table.add_column("First", style="cyan")
    table.add_column("Last", style="cyan")
    table.add_column("ID", style="dim")

    for t in active[:limit]:
        entries = loop.run_until_complete(store.get_thread_entries(t.id))
        first = min(e.entry_date for e in entries).strftime("%Y-%m-%d") if entries else "?"
        last = max(e.entry_date for e in entries).strftime("%Y-%m-%d") if entries else "?"
        table.add_row(t.label[:50], str(t.entry_count), first, last, t.id[:8])

    console.print(table)


@threads.command("reindex")
def threads_reindex():
    """Rebuild all threads from scratch using current similarity threshold."""
    c = get_components(skip_advisor=True)

    from journal.threads import ThreadDetector

    threads_cfg = c["config_model"].threads
    store = get_thread_store(c["config"], c.get("storage_paths"))
    detector = ThreadDetector(
        c["embeddings"],
        store,
        {
            "similarity_threshold": threads_cfg.similarity_threshold,
            "candidate_count": threads_cfg.candidate_count,
            "min_entries_for_thread": threads_cfg.min_entries_for_thread,
        },
    )

    with console.status("Rebuilding threads..."):
        loop = asyncio.get_event_loop()
        stats = loop.run_until_complete(detector.reindex_all())

    console.print(f"[green]Reindex complete:[/] {stats['entries_processed']} entries processed")
    console.print(
        f"  {stats['threads_created']} threads created, "
        f"{stats['entries_threaded']} entries threaded"
    )
