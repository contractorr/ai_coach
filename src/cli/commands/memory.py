"""Memory CLI commands — status, list, search, inspect, delete, backfill, reset."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from cli.utils import get_components, get_memory_store

console = Console()


def _get_store(c):
    return get_memory_store(c["config"], storage_paths=c.get("storage_paths"))


@click.group()
def memory():
    """Distilled memory — facts extracted from journal entries."""
    pass


@memory.command("status")
def memory_status():
    """Show fact counts by category and total."""
    c = get_components(skip_advisor=True)
    store = _get_store(c)
    stats = store.get_stats()

    console.print(f"Active facts: {stats['total_active']}")
    console.print(f"Superseded: {stats['total_superseded']}")
    if stats["by_category"]:
        console.print("\nBy category:")
        for cat, cnt in sorted(stats["by_category"].items()):
            console.print(f"  {cat}: {cnt}")


@memory.command("list")
@click.option("--category", "-c", default=None, help="Filter by category")
def memory_list(category: str | None):
    """List all active facts, grouped by category."""
    c = get_components(skip_advisor=True)
    store = _get_store(c)

    if category:
        from memory.models import FactCategory

        try:
            cat = FactCategory(category)
        except ValueError:
            console.print(f"[red]Unknown category: {category}[/]")
            console.print(f"Valid: {[c.value for c in FactCategory]}")
            return
        facts = store.get_by_category(cat)
    else:
        facts = store.get_all_active()

    if not facts:
        console.print("No facts stored.")
        return

    table = Table(title="Steward Facts")
    table.add_column("ID", style="dim", width=8)
    table.add_column("Category", width=12)
    table.add_column("Fact")
    table.add_column("Conf", width=5)
    table.add_column("Source", width=10)

    for f in facts:
        table.add_row(
            f.id[:8],
            f.category.value,
            f.text[:80],
            f"{f.confidence:.1f}",
            f"{f.source_type.value}:{f.source_id[:12]}",
        )

    console.print(table)


@memory.command("search")
@click.argument("query")
@click.option("--limit", "-n", default=10)
def memory_search(query: str, limit: int):
    """Semantic search over facts."""
    c = get_components(skip_advisor=True)
    store = _get_store(c)
    facts = store.search(query, limit=limit)

    if not facts:
        console.print("No matching facts.")
        return

    for f in facts:
        console.print(f"[dim]{f.id[:8]}[/] [{f.category.value}] {f.text} (conf={f.confidence:.1f})")


@memory.command("inspect")
@click.argument("fact_id")
def memory_inspect(fact_id: str):
    """Show fact details and supersession history."""
    c = get_components(skip_advisor=True)
    store = _get_store(c)
    fact = store.get(fact_id)
    if not fact:
        console.print(f"[red]Fact not found: {fact_id}[/]")
        return

    console.print(f"ID: {fact.id}")
    console.print(f"Text: {fact.text}")
    console.print(f"Category: {fact.category.value}")
    console.print(f"Source: {fact.source_type.value}:{fact.source_id}")
    console.print(f"Confidence: {fact.confidence}")
    console.print(f"Created: {fact.created_at}")
    console.print(f"Updated: {fact.updated_at}")
    console.print(f"Superseded by: {fact.superseded_by or 'none (active)'}")

    history = store.get_history(fact_id)
    if len(history) > 1:
        console.print("\nHistory chain:")
        for h in history:
            status = "active" if h.superseded_by is None else f"-> {h.superseded_by[:8]}"
            console.print(f"  {h.id[:8]} | {h.text[:60]} | {status}")


@memory.command("delete")
@click.argument("fact_id")
@click.confirmation_option(prompt="Delete this fact?")
def memory_delete(fact_id: str):
    """Soft-delete a fact."""
    c = get_components(skip_advisor=True)
    store = _get_store(c)
    fact = store.get(fact_id)
    if not fact:
        console.print(f"[red]Fact not found: {fact_id}[/]")
        return
    store.delete(fact_id, reason="manual_cli")
    console.print(f"Deleted fact {fact_id[:8]}")


@memory.command("backfill")
@click.option("--dry-run", is_flag=True, help="Show what would be extracted without storing")
def memory_backfill(dry_run: bool):
    """Extract facts from all existing journal entries."""
    c = get_components(skip_advisor=True)
    config = c["config"]
    store = _get_store(c)

    from journal.storage import JournalStorage

    journal_dir = Path(config["paths"]["journal_dir"]).expanduser()
    storage = JournalStorage(journal_dir)
    entries = storage.list_entries(limit=1000)

    # Load content for each entry
    full_entries = []
    for e in entries:
        try:
            post = storage.read(e["path"])
            full_entries.append(
                {
                    "path": str(e["path"]),
                    "content": post.content,
                    "type": e.get("type", ""),
                    "tags": e.get("tags", []),
                    "created": e.get("created", ""),
                }
            )
        except Exception:
            continue

    console.print(f"Found {len(full_entries)} journal entries")

    if dry_run:
        from memory.extractor import FactExtractor

        extractor = FactExtractor(
            max_facts_per_entry=config.get("memory", {}).get("max_facts_per_entry", 5)
        )
        total = 0
        for entry in sorted(full_entries, key=lambda e: e.get("created", "")):
            facts = extractor.extract_from_journal(
                entry["path"], entry["content"], {"type": entry["type"], "tags": entry["tags"]}
            )
            for f in facts:
                console.print(f"  [{f.category.value}] {f.text} (conf={f.confidence:.1f})")
            total += len(facts)
        console.print(f"\n[yellow]Dry run:[/] would extract {total} facts")
        return

    from memory.pipeline import MemoryPipeline

    consolidator = None
    consolidation_cfg = config.get("memory", {}).get("consolidation", {})
    if consolidation_cfg.get("enabled", True):
        try:
            from memory.consolidator import ObservationConsolidator

            consolidator = ObservationConsolidator(
                store,
                min_facts_per_group=consolidation_cfg.get("min_facts_per_group", 2),
            )
        except Exception:
            pass
    pipeline = MemoryPipeline(store, consolidator=consolidator)
    stats = pipeline.backfill(full_entries)
    console.print(f"Processed: {stats['entries_processed']}")
    console.print(f"Extracted: {stats['facts_extracted']}")
    console.print(f"Stored: {stats['facts_stored']}")


@memory.command("reset")
@click.confirmation_option(prompt="Delete ALL facts? This cannot be undone.")
def memory_reset():
    """Delete all facts."""
    c = get_components(skip_advisor=True)
    store = _get_store(c)
    count = store.reset()
    console.print(f"Deleted {count} facts")
