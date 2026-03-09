"""Intelligence CLI commands."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from cli.utils import get_components, get_watchlist_store
from intelligence.scheduler import IntelScheduler

console = Console()


def _get_watchlist_store():
    c = get_components(skip_advisor=True)
    return get_watchlist_store(c["config"], c.get("storage_paths"))


@click.command()
def scrape():
    """Run intelligence gathering now."""
    c = get_components(skip_advisor=True)
    scheduler = IntelScheduler(c["intel_storage"], c["config"].get("sources", {}))

    with console.status("Gathering intelligence..."):
        results = scheduler.run_now()

    # Sync to embeddings for semantic search
    with console.status("Syncing embeddings..."):
        c["intel_search"].sync_embeddings()

    table = Table(show_header=True)
    table.add_column("Source")
    table.add_column("Scraped", justify="right")
    table.add_column("New", justify="right", style="green")
    table.add_column("Deduped", justify="right", style="yellow")

    for source, data in results.items():
        if "error" in data:
            table.add_row(source, "[red]error[/]", data["error"][:30], "")
        else:
            table.add_row(
                source, str(data["scraped"]), str(data["new"]), str(data.get("deduped", 0))
            )

    console.print(table)


@click.command()
@click.option("-n", "--days", default=7, help="Days to look back")
@click.option("--limit", default=20, help="Max items to show")
def brief(days: int, limit: int):
    """Show recent intelligence brief."""
    c = get_components(skip_advisor=True)
    items = c["intel_storage"].get_recent(days=days, limit=limit)

    if not items:
        console.print("[yellow]No intelligence items found. Run 'coach scrape' first.[/]")
        return

    for item in items:
        console.print(f"\n[cyan]{item['title'][:60]}[/]")
        console.print(f"[dim]{item['source']} | {item['scraped_at'][:10]}[/]")
        if item["summary"]:
            console.print(item["summary"][:150])
        console.print(f"[blue]{item['url']}[/]")


@click.command()
def sources():
    """Show configured intelligence sources."""
    c = get_components(skip_advisor=True)
    sources_config = c["config"].get("sources", {})

    console.print("\n[bold]Enabled sources:[/]")
    for src in sources_config.get("enabled", []):
        console.print(f"  [green]✓[/] {src}")

    console.print("\n[bold]RSS Feeds:[/]")
    for url in sources_config.get("rss_feeds", []):
        console.print(f"  {url}")

    console.print("\n[bold]Custom Blogs:[/]")
    for url in sources_config.get("custom_blogs", []):
        console.print(f"  {url}")


@click.command()
@click.option("-n", "--days", default=7, help="Lookback window in days")
@click.option("--min-sources", default=2, help="Min distinct sources per topic")
@click.option("--limit", default=15, help="Max topics to show")
@click.option("--refresh", is_flag=True, help="Force recompute (ignore cache)")
def radar(days: int, min_sources: int, limit: int, refresh: bool):
    """Show cross-source trending topics."""
    c = get_components(skip_advisor=True)

    from intelligence.trending_radar import TrendingRadar

    tr = TrendingRadar(c["intel_storage"].db_path)

    with console.status("Computing trending topics..."):
        if refresh:
            snapshot = tr.refresh(days=days, min_sources=min_sources, max_topics=limit)
        else:
            snapshot = tr.get_or_compute(days=days, min_sources=min_sources, max_topics=limit)

    topics = snapshot.get("topics", [])
    if not topics:
        console.print("[yellow]No cross-source trending topics found. Run 'coach scrape' first.[/]")
        return

    console.print(
        f"[dim]{snapshot['total_items_scanned']} items scanned ({snapshot['days']}d window)[/]\n"
    )

    for i, t in enumerate(topics, 1):
        score_bar = "█" * int(t["score"] * 20)
        console.print(
            f"[bold]{i:>2}. {t['topic']}[/]  "
            f"[green]{score_bar}[/] {t['score']:.2f}  "
            f"[dim]{t['item_count']} items, {t['source_count']} sources[/]"
        )
        console.print(f"    [cyan]{', '.join(t['sources'])}[/]")
        if t.get("items"):
            top = t["items"][0]
            console.print(f"    [blue]{top['title'][:70]}[/]")
            console.print(f"    [dim]{top['url']}[/]")
        console.print()


@click.command("scraper-health")
def scraper_health():
    """Show per-source scraper health metrics."""
    from intelligence.health import ScraperHealthTracker

    c = get_components(skip_advisor=True)
    tracker = ScraperHealthTracker(c["intel_storage"].db_path)
    rows = tracker.get_health_summary()

    if not rows:
        console.print("[yellow]No scraper health data. Run 'coach scrape' first.[/]")
        return

    table = Table(show_header=True, title="Scraper Health")
    table.add_column("Source")
    table.add_column("Status")
    table.add_column("Last Success")
    table.add_column("Items", justify="right")
    table.add_column("New", justify="right")
    table.add_column("Deduped", justify="right")
    table.add_column("Duration", justify="right")
    table.add_column("Errors", justify="right")
    table.add_column("Error Rate", justify="right")
    table.add_column("Last Error")

    status_style = {"healthy": "green", "degraded": "yellow", "failing": "red", "backoff": "red"}

    for r in rows:
        status = r.get("status", "?")
        style = status_style.get(status, "white")
        last_success = (r.get("last_success_at") or "-")[:19]
        duration = f"{r['last_duration_seconds']:.1f}s" if r.get("last_duration_seconds") else "-"
        last_err = (r.get("last_error") or "-")[:40]
        table.add_row(
            r["source"],
            f"[{style}]{status}[/{style}]",
            last_success,
            str(r.get("last_items_scraped", 0)),
            str(r.get("last_items_new", 0)),
            str(r.get("last_items_deduped", 0)),
            duration,
            str(r.get("total_errors", 0)),
            f"{r.get('error_rate', 0):.1f}%",
            last_err,
        )

    console.print(table)


@click.command("intel-export")
@click.option("-o", "--output", required=True, type=click.Path(), help="Output file path")
@click.option(
    "-f",
    "--format",
    "fmt",
    default="json",
    type=click.Choice(["json", "csv", "markdown"]),
    help="Export format",
)
@click.option("-d", "--days", type=int, default=30, help="Only last N days")
@click.option("-s", "--source", help="Filter by source")
@click.option("-n", "--limit", type=int, help="Max items to export")
def intel_export(output: str, fmt: str, days: int, source: str, limit: int):
    """Export intelligence items to file."""
    from intelligence.export import IntelExporter

    c = get_components(skip_advisor=True)
    exporter = IntelExporter(c["intel_storage"])

    output_path = Path(output)

    with console.status(f"Exporting to {fmt}..."):
        if fmt == "json":
            count = exporter.export_json(output_path, days=days, source=source, limit=limit)
        elif fmt == "csv":
            count = exporter.export_csv(output_path, days=days, source=source, limit=limit)
        else:
            count = exporter.export_markdown(output_path, days=days, source=source, limit=limit)

    console.print(f"[green]Exported {count} items to {output_path}[/]")


@click.command("dedup-backfill")
@click.option("-d", "--days", default=30, help="Lookback window in days")
@click.option("-t", "--threshold", default=0.92, help="Similarity threshold (0-1)")
@click.option("--dry-run", is_flag=True, help="Show what would be deduped without writing")
def dedup_backfill(days: int, threshold: float, dry_run: bool):
    """Backfill semantic dedup: scan recent items and mark near-duplicates."""
    from db import wal_connect
    from intelligence.embeddings import IntelEmbeddingManager

    c = get_components(skip_advisor=True)
    storage = c["intel_storage"]
    paths_config = c["config"].get("paths", {})
    chroma_dir = Path(paths_config.get("chroma_dir", "~/coach/chroma")).expanduser()

    em = IntelEmbeddingManager(chroma_dir)

    with wal_connect(storage.db_path) as conn:
        conn.row_factory = __import__("sqlite3").Row
        rows = conn.execute(
            """SELECT id, title, summary, source FROM intel_items
               WHERE scraped_at >= datetime('now', ?) AND duplicate_of IS NULL
               ORDER BY id""",
            (f"-{days} days",),
        ).fetchall()

    total = len(rows)
    deduped = 0

    with console.status(f"Scanning {total} items (threshold={threshold})..."):
        for row in rows:
            content = f"{row['title']} {row['summary'] or ''}"
            canonical_id = em.find_similar(content, threshold=threshold)
            if canonical_id and canonical_id != str(row["id"]):
                deduped += 1
                if dry_run:
                    console.print(
                        f"[yellow]would dedup[/] #{row['id']} -> #{canonical_id}: "
                        f"{row['title'][:60]}"
                    )
                else:
                    storage.mark_duplicate(row["id"], int(canonical_id))
            else:
                # Index for subsequent comparisons
                em.add_item(str(row["id"]), content, {"source": row["source"]})

    action = "would mark" if dry_run else "marked"
    console.print(f"[green]Done:[/] {action} {deduped}/{total} items as duplicates")


@click.group()
def watchlist():
    """Manage tracked entities and themes for bespoke intel ranking."""


@watchlist.command("list")
def watchlist_list():
    """List watchlist items."""
    items = _get_watchlist_store().list_items()
    if not items:
        console.print("[yellow]No watchlist items yet. Add one with 'coach watchlist add'.[/]")
        return

    table = Table(show_header=True, title="Watchlist")
    table.add_column("ID", style="dim")
    table.add_column("Label", style="cyan")
    table.add_column("Kind")
    table.add_column("Priority")
    table.add_column("Why")

    for item in items:
        table.add_row(
            item["id"],
            item["label"],
            item.get("kind", "theme"),
            item.get("priority", "medium"),
            (item.get("why") or "")[:60],
        )

    console.print(table)


@watchlist.command("add")
@click.argument("label")
@click.option("--kind", default="theme", help="Item type, e.g. company or technology")
@click.option("--priority", default="medium", type=click.Choice(["high", "medium", "low"]))
@click.option("--why", default="", help="Why this matters to you")
@click.option("--alias", "aliases", multiple=True, help="Alternate term; can be repeated")
@click.option("--tag", "tags", multiple=True, help="Tag; can be repeated")
@click.option("--goal", default="", help="Optional linked goal")
@click.option("--time-horizon", default="quarter", help="Optional horizon label")
@click.option("--source", "sources", multiple=True, help="Preferred source; can be repeated")
def watchlist_add(
    label: str,
    kind: str,
    priority: str,
    why: str,
    aliases: tuple[str, ...],
    tags: tuple[str, ...],
    goal: str,
    time_horizon: str,
    sources: tuple[str, ...],
):
    """Add a watchlist item."""
    item = _get_watchlist_store().save_item(
        {
            "label": label,
            "kind": kind,
            "priority": priority,
            "why": why,
            "aliases": list(aliases),
            "tags": list(tags),
            "goal": goal,
            "time_horizon": time_horizon,
            "source_preferences": list(sources),
        }
    )
    console.print(f"[green]Saved[/] watchlist item {item['label']} ({item['id']})")


@watchlist.command("update")
@click.argument("item_id")
@click.option("--label", default=None)
@click.option("--kind", default=None)
@click.option("--priority", default=None, type=click.Choice(["high", "medium", "low"]))
@click.option("--why", default=None)
@click.option("--aliases", default=None, help="Comma-separated aliases")
@click.option("--tags", default=None, help="Comma-separated tags")
@click.option("--goal", default=None)
@click.option("--time-horizon", default=None)
@click.option("--sources", default=None, help="Comma-separated preferred sources")
def watchlist_update(
    item_id: str,
    label: str | None,
    kind: str | None,
    priority: str | None,
    why: str | None,
    aliases: str | None,
    tags: str | None,
    goal: str | None,
    time_horizon: str | None,
    sources: str | None,
):
    """Update a watchlist item."""
    updates = {
        key: value
        for key, value in {
            "label": label,
            "kind": kind,
            "priority": priority,
            "why": why,
            "aliases": [part.strip() for part in aliases.split(",")]
            if aliases is not None
            else None,
            "tags": [part.strip() for part in tags.split(",")] if tags is not None else None,
            "goal": goal,
            "time_horizon": time_horizon,
            "source_preferences": [part.strip() for part in sources.split(",")]
            if sources is not None
            else None,
        }.items()
        if value is not None
    }
    item = _get_watchlist_store().update_item(item_id, updates)
    if not item:
        console.print(f"[red]Watchlist item not found:[/] {item_id}")
        raise SystemExit(1)
    console.print(f"[green]Updated[/] watchlist item {item['label']} ({item['id']})")


@watchlist.command("remove")
@click.argument("item_id")
def watchlist_remove(item_id: str):
    """Remove a watchlist item."""
    deleted = _get_watchlist_store().delete_item(item_id)
    if not deleted:
        console.print(f"[red]Watchlist item not found:[/] {item_id}")
        raise SystemExit(1)
    console.print(f"[green]Removed[/] watchlist item {item_id}")
