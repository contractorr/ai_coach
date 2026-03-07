"""Database health check and rebuild commands."""

import click
from rich.console import Console
from rich.table import Table

console = Console()

COLLECTIONS = ("journal", "intel")


def _get_db_components(collection: str):
    """Lightweight init of embedding + search components for given collection."""
    from cli.config import get_paths, load_config
    from cli.utils import get_intel_storage, get_storage_paths
    from intelligence.embeddings import IntelEmbeddingManager
    from intelligence.search import IntelSearch
    from journal import EmbeddingManager, JournalSearch, JournalStorage

    config = load_config()
    paths = get_paths(config)

    result = {}

    if collection in ("journal", "all"):
        from journal.fts import JournalFTSIndex

        storage = JournalStorage(paths["journal_dir"])
        embeddings = EmbeddingManager(paths["chroma_dir"])
        fts_index = JournalFTSIndex(paths["journal_dir"])
        search = JournalSearch(storage, embeddings, fts_index=fts_index)
        result["journal"] = {
            "storage": storage,
            "embeddings": embeddings,
            "search": search,
            "source_count": len(storage.list_entries()),
        }

    if collection in ("intel", "all"):
        import sqlite3

        intel_storage = get_intel_storage(config, storage_paths=get_storage_paths(config=config, paths=paths))
        intel_embeddings = IntelEmbeddingManager(paths["chroma_dir"] / "intel")
        intel_search = IntelSearch(intel_storage, intel_embeddings)
        # Count rows directly — IntelStorage has no count() method
        try:
            with sqlite3.connect(str(paths["intel_db"])) as conn:
                source_count = conn.execute("SELECT COUNT(*) FROM intel_items").fetchone()[0]
        except Exception:
            source_count = 0
        result["intel"] = {
            "storage": intel_storage,
            "embeddings": intel_embeddings,
            "search": intel_search,
            "source_count": source_count,
        }

    return result


@click.group()
def db():
    """Database health check and rebuild commands."""
    pass


@db.command()
@click.option(
    "--collection",
    type=click.Choice(["journal", "intel", "all"]),
    default="all",
    help="Collection to check",
)
def check(collection: str):
    """Check ChromaDB health and compare with source data."""
    components = _get_db_components(collection)

    table = Table(title="ChromaDB Health Check", show_header=True)
    table.add_column("Collection")
    table.add_column("Status", justify="center")
    table.add_column("Embeddings", justify="right")
    table.add_column("Source", justify="right")
    table.add_column("Model")

    for name, comp in components.items():
        health = comp["embeddings"].health_check()
        source_count = comp["source_count"]
        embed_count = health["count"]

        if health["status"] == "error":
            status = "[red]error[/]"
        elif embed_count == source_count:
            status = "[green]ok[/]"
        elif embed_count == 0:
            status = "[red]empty[/]"
        else:
            status = "[yellow]drift[/]"

        model = health["model"]
        if model == "unknown":
            model = "[yellow]unknown (pre-tracking)[/]"

        table.add_row(
            name,
            status,
            str(embed_count),
            str(source_count),
            model,
        )

    console.print(table)

    # Print warnings
    for name, comp in components.items():
        health = comp["embeddings"].health_check()
        if health["status"] == "error":
            console.print(f"[red]Error in {name}:[/] {health.get('error', 'unknown')}")
            console.print(f"  Run: [bold]coach db rebuild --collection {name}[/]")
        elif health["count"] != comp["source_count"]:
            console.print(f"[yellow]{name}: embedding/source count mismatch[/]")
            console.print(f"  Run: [bold]coach db rebuild --collection {name}[/]")


@db.command()
@click.option(
    "--collection",
    type=click.Choice(["journal", "intel", "all"]),
    default="all",
    help="Collection to rebuild",
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def rebuild(collection: str, yes: bool):
    """Delete and rebuild ChromaDB embeddings from source data."""
    targets = [collection] if collection != "all" else list(COLLECTIONS)

    if not yes:
        names = ", ".join(targets)
        click.confirm(f"Rebuild embeddings for: {names}? This deletes existing vectors", abort=True)

    components = _get_db_components(collection)

    for name in targets:
        if name not in components:
            continue
        comp = components[name]

        console.print(f"\n[bold]Rebuilding {name}...[/]")

        # Delete and recreate collection
        comp["embeddings"].delete_collection()
        console.print("  Deleted collection")

        # Re-embed from source
        with console.status(f"  Re-embedding {name}..."):
            added, removed = comp["search"].sync_embeddings()

        console.print(f"  Synced: {added} added, {removed} removed")

    # Final summary
    console.print()
    refreshed = _get_db_components(collection)
    for name, comp in refreshed.items():
        health = comp["embeddings"].health_check()
        console.print(f"[green]{name}:[/] {health['count']} embeddings, model={health['model']}")
