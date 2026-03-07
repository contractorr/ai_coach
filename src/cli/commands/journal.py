"""Journal CLI commands."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import structlog
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from cli.utils import get_components, get_thread_store

console = Console()
logger = structlog.get_logger()


def resolve_journal_path(journal_dir: Path, filename: str) -> Optional[Path]:
    """Resolve and validate a journal file path.

    Returns resolved Path if valid and found, None otherwise.
    """
    filepath = (journal_dir / filename).resolve()

    if not filepath.is_relative_to(journal_dir):
        return None

    if filepath.exists():
        return filepath

    # Glob fallback for partial match
    matches = [
        m for m in journal_dir.glob(f"*{filename}*") if m.resolve().is_relative_to(journal_dir)
    ]
    return matches[0] if matches else None


def _run_thread_detection(c: dict, entry_id: str) -> None:
    """Post-write hook: run thread detection and print result."""
    try:
        threads_cfg = c["config_model"].threads
        if not threads_cfg.enabled:
            return

        # Get embedding for the entry
        result = c["embeddings"].collection.get(ids=[entry_id], include=["embeddings"])
        if not result["embeddings"] or not result["embeddings"][0]:
            return
        embedding = result["embeddings"][0]

        # Parse entry date from filename or use now
        entry_date = datetime.now()
        try:
            entry = c["storage"].read(Path(entry_id))
            created = entry.get("created", "")
            if created:
                entry_date = datetime.fromisoformat(str(created).replace("Z", "+00:00")).replace(
                    tzinfo=None
                )
        except Exception:
            pass

        from journal.threads import ThreadDetector

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

        match = asyncio.get_event_loop().run_until_complete(
            detector.detect(entry_id, embedding, entry_date)
        )

        if match.match_type == "joined_existing":
            thread = asyncio.get_event_loop().run_until_complete(store.get_thread(match.thread_id))
            entries = asyncio.get_event_loop().run_until_complete(
                store.get_thread_entries(match.thread_id)
            )
            dates = sorted(
                set(te.entry_date.strftime("%b %-d") for te in entries if te.entry_id != entry_id)
            )
            first_date = entries[0].entry_date if entries else entry_date
            console.print(
                f"[dim]🔄 You've written about this {thread.entry_count} times since "
                f"{first_date.strftime('%b %-d')} — thread includes entries from {', '.join(dates[:5])}[/]"
            )
        elif match.match_type == "created_new":
            thread = asyncio.get_event_loop().run_until_complete(store.get_thread(match.thread_id))
            entries = asyncio.get_event_loop().run_until_complete(
                store.get_thread_entries(match.thread_id)
            )
            other_dates = sorted(
                set(te.entry_date.strftime("%b %-d") for te in entries if te.entry_id != entry_id)
            )
            console.print(
                f"[dim]🔄 New pattern detected — this connects with "
                f"{len(other_dates)} earlier entries ({', '.join(other_dates[:5])})[/]"
            )
    except Exception as e:
        logger.debug("thread_detection_failed", error=str(e))


@click.group()
def journal():
    """Manage journal entries."""
    pass


@journal.command("add")
@click.option(
    "-t",
    "--type",
    "entry_type",
    default="daily",
    type=click.Choice(["daily", "project", "goal", "reflection"]),
    help="Entry type",
)
@click.option("--title", help="Entry title (defaults to date)")
@click.option("--tags", help="Comma-separated tags")
@click.option(
    "--template", "template_name", help="Use template (daily, weekly, goal, project, learning)"
)
@click.argument("content", required=False)
def journal_add(entry_type: str, title: str, tags: str, template_name: str, content: str):
    """Add new journal entry. Opens editor if no content provided."""
    c = get_components()

    if not content:
        initial = "# Write your entry here\n\n"
        if template_name:
            from journal.templates import get_template

            custom = c["config"].get("journal", {}).get("templates", {})
            tmpl = get_template(template_name, custom)
            if tmpl:
                entry_type = tmpl.get("type", entry_type)
                initial = f"# {tmpl['name']}\n\n{tmpl['content']}"
            else:
                console.print(f"[yellow]Unknown template '{template_name}'[/]")
                return
        content = click.edit(initial)
        if not content:
            console.print("[yellow]No content provided, cancelled.[/]")
            return

    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    filepath = c["storage"].create(
        content=content,
        entry_type=entry_type,
        title=title,
        tags=tag_list,
        metadata={},
    )

    # Add to embeddings
    c["embeddings"].add_entry(
        str(filepath),
        content,
        {"type": entry_type, "tags": ",".join(tag_list)},
    )

    console.print(f"[green]Created:[/] {filepath.name}")

    # Thread detection
    _run_thread_detection(c, str(filepath))


@journal.command("list")
@click.option("-t", "--type", "entry_type", help="Filter by type")
@click.option("--tag", help="Filter by tag")
@click.option("-n", "--limit", default=10, help="Max entries to show")
def journal_list(entry_type: str, tag: str, limit: int):
    """List recent journal entries."""
    c = get_components(skip_advisor=True)
    entries = c["storage"].list_entries(entry_type=entry_type, limit=limit)

    # Filter by tag if specified
    if tag:
        entries = [e for e in entries if tag in e.get("tags", [])]

    if not entries:
        console.print("[yellow]No entries found.[/]")
        return

    table = Table(show_header=True)
    table.add_column("Date", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Title")
    table.add_column("Tags", style="dim")

    for e in entries:
        date = e["created"][:10] if e["created"] else "?"
        tags = ", ".join(e["tags"][:3]) if e["tags"] else ""
        table.add_row(date, e["type"], e["title"][:40], tags)

    console.print(table)


@journal.command("search")
@click.argument("query")
@click.option("-n", "--limit", default=5, help="Max results")
def journal_search(query: str, limit: int):
    """Semantic search across journal."""
    c = get_components()

    with console.status("Searching..."):
        results = c["search"].semantic_search(query, n_results=limit)

    if not results:
        console.print("[yellow]No matches found.[/]")
        return

    for r in results:
        score = f"{r['relevance']:.0%}"
        console.print(f"\n[cyan]{r['title']}[/] ({r['type']}) - {score} match")
        console.print(f"[dim]{r['created'][:10] if r['created'] else ''}[/]")
        preview = r["content"][:200].replace("\n", " ")
        console.print(f"{preview}...")


@journal.command("sync")
def journal_sync():
    """Sync all entries to embedding store."""
    c = get_components()

    with console.status("Syncing embeddings..."):
        added, removed = c["search"].sync_embeddings()

    console.print(f"[green]Synced:[/] {added} added, {removed} removed")
    console.print(f"Total entries: {c['embeddings'].count()}")


@journal.command("export")
@click.option("-o", "--output", required=True, type=click.Path(), help="Output file path")
@click.option(
    "-f",
    "--format",
    "fmt",
    default="json",
    type=click.Choice(["json", "markdown"]),
    help="Export format",
)
@click.option("-t", "--type", "entry_type", help="Filter by entry type")
@click.option("-d", "--days", type=int, help="Only last N days")
@click.option("-n", "--limit", type=int, help="Max entries to export")
def journal_export(output: str, fmt: str, entry_type: str, days: int, limit: int):
    """Export journal entries to file."""
    from journal.export import JournalExporter

    c = get_components(skip_advisor=True)
    exporter = JournalExporter(c["storage"])

    output_path = Path(output)

    with console.status(f"Exporting to {fmt}..."):
        if fmt == "json":
            count = exporter.export_json(output_path, entry_type=entry_type, days=days, limit=limit)
        else:
            count = exporter.export_markdown(
                output_path, entry_type=entry_type, days=days, limit=limit
            )

    console.print(f"[green]Exported {count} entries to {output_path}[/]")


@journal.command("view")
@click.argument("filename")
def journal_view(filename: str):
    """View a journal entry."""
    c = get_components()
    journal_dir = c["paths"]["journal_dir"].resolve()
    filepath = resolve_journal_path(journal_dir, filename)
    if filepath is None:
        console.print(f"[red]Not found:[/] {filename}")
        return

    post = c["storage"].read(filepath)
    console.print(f"\n[cyan bold]{post.get('title', filepath.stem)}[/]")
    console.print(f"[dim]Type: {post.get('type')} | Created: {post.get('created', '?')[:10]}[/]")
    if post.get("tags"):
        console.print(f"[dim]Tags: {', '.join(post['tags'])}[/]")
    console.print()
    console.print(Markdown(post.content))


@journal.command("edit")
@click.argument("filename")
def journal_edit(filename: str):
    """Edit a journal entry in $EDITOR."""
    import os
    import subprocess

    c = get_components(skip_advisor=True)
    journal_dir = c["paths"]["journal_dir"].resolve()
    filepath = resolve_journal_path(journal_dir, filename)
    if filepath is None:
        console.print(f"[red]Not found:[/] {filename}")
        return

    editor = os.environ.get("EDITOR", "vim")
    try:
        subprocess.run([editor, str(filepath)], check=True)
        # Re-sync embeddings after edit
        post = c["storage"].read(filepath)
        c["embeddings"].add_entry(
            str(filepath),
            post.content,
            {"type": post.get("type", ""), "tags": ",".join(post.get("tags", []))},
        )
        console.print(f"[green]Updated:[/] {filepath.name}")
    except subprocess.CalledProcessError:
        console.print("[red]Editor exited with error[/]")
    except FileNotFoundError:
        console.print(f"[red]Editor not found:[/] {editor}")


@journal.command("delete")
@click.argument("filename")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def journal_delete(filename: str, yes: bool):
    """Delete a journal entry."""
    c = get_components(skip_advisor=True)
    journal_dir = c["paths"]["journal_dir"].resolve()
    filepath = resolve_journal_path(journal_dir, filename)
    if filepath is None:
        console.print(f"[red]Not found:[/] {filename}")
        return

    if not yes:
        if not click.confirm(f"Delete {filepath.name}?"):
            return

    filepath.unlink()
    c["embeddings"].delete_entry(str(filepath))
    console.print(f"[green]Deleted:[/] {filepath.name}")
