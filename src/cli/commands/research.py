"""Research CLI commands."""

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from cli.utils import get_components
from intelligence.scheduler import IntelScheduler

console = Console()


def _get_scheduler(skip_advisor: bool = False) -> IntelScheduler:
    c = get_components(skip_advisor=skip_advisor)
    return IntelScheduler(
        c["intel_storage"],
        c["config"].get("sources", {}),
        journal_storage=c["storage"],
        embeddings=c["embeddings"],
        full_config=c["config"],
    )


@click.group()
def research():
    """Deep research on topics from your goals and journal."""
    from cli.utils import warn_experimental

    warn_experimental("Deep research")


@research.command("run")
@click.option("--topic", "-t", help="Specific topic to research (overrides auto-selection)")
@click.option("--dossier", "dossier_id", help="Update a persistent dossier by ID")
def research_run(topic: str | None, dossier_id: str | None):
    """Run deep research on selected topics or an existing dossier."""
    c = get_components()
    scheduler = IntelScheduler(
        c["intel_storage"],
        c["config"].get("sources", {}),
        journal_storage=c["storage"],
        embeddings=c["embeddings"],
        full_config=c["config"],
    )

    if not c["config"].get("research", {}).get("enabled", False):
        console.print("[yellow]Research not enabled. Add 'research.enabled: true' to config.yaml[/]")
        return

    with console.status("Running deep research..."):
        results = scheduler.run_research_now(topic=topic, dossier_id=dossier_id)

    if not results:
        console.print("[yellow]No topics to research or research not configured.[/]")
        return

    for result in results:
        if result.get("success"):
            saved = result.get("filepath") or result.get("saved_path")
            name = saved.name if saved else "N/A"
            prefix = f"{result['topic']}"
            if result.get("dossier_id"):
                prefix = f"{prefix} [{result['dossier_id']}]"
            console.print(f"[green]✓[/] {prefix} -> {name}")
        else:
            console.print(f"[red]✗[/] {result.get('topic', 'unknown')}: {result.get('error', 'Unknown error')}")


@research.command("topics")
def research_topics():
    """Show suggested research topics based on your goals and journal."""
    c = get_components(skip_advisor=True)
    scheduler = IntelScheduler(
        c["intel_storage"],
        c["config"].get("sources", {}),
        journal_storage=c["storage"],
        embeddings=c["embeddings"],
        full_config=c["config"],
    )

    if "research" not in c["config"]:
        c["config"]["research"] = {}
    c["config"]["research"]["enabled"] = True

    topics = scheduler.get_research_topics()
    if not topics:
        console.print("[yellow]No research topics identified. Add goals or journal entries.[/]")
        return

    table = Table(show_header=True, title="Suggested Research Topics")
    table.add_column("Topic", style="cyan")
    table.add_column("Source", style="green")
    table.add_column("Score", justify="right")
    table.add_column("Reason")
    for topic in topics:
        table.add_row(topic["topic"], topic["source"], str(topic["score"]), topic["reason"][:50])
    console.print(table)


@research.command("list")
@click.option("-n", "--limit", default=10, help="Max entries to show")
def research_list(limit: int):
    """List recent research reports."""
    c = get_components(skip_advisor=True)
    entries = c["storage"].list_entries(entry_type="research", limit=limit)

    if not entries:
        console.print("[yellow]No research reports yet. Run 'coach research run' first.[/]")
        return

    table = Table(show_header=True)
    table.add_column("Date", style="cyan")
    table.add_column("Topic")
    table.add_column("Tags", style="dim")
    for entry in entries:
        date = entry["created"][:10] if entry["created"] else "?"
        topic = entry["title"].replace("Research: ", "")
        tags = ", ".join(entry["tags"][:3]) if entry["tags"] else ""
        table.add_row(date, topic[:40], tags)
    console.print(table)


@research.command("view")
@click.argument("filename")
def research_view(filename: str):
    """View a research report."""
    c = get_components(skip_advisor=True)
    journal_dir = c["paths"]["journal_dir"].resolve()
    matches = [
        match for match in journal_dir.glob(f"*research*{filename}*") if match.resolve().is_relative_to(journal_dir)
    ]
    if not matches:
        matches = [match for match in journal_dir.glob(f"*{filename}*") if match.resolve().is_relative_to(journal_dir)]
    if not matches:
        console.print(f"[red]Not found:[/] {filename}")
        return

    filepath = matches[0]
    post = c["storage"].read(filepath)
    console.print(f"\n[cyan bold]{post.get('title', filepath.stem)}[/]")
    console.print(f"[dim]Created: {post.get('created', '?')[:10]}[/]")
    if post.get("topic"):
        console.print(f"[dim]Topic: {post['topic']}[/]")
    console.print()
    console.print(Markdown(post.content))


@research.command("dossiers")
@click.option("-n", "--limit", default=20, help="Max dossiers to show")
@click.option("--all", "include_archived", is_flag=True, help="Include archived dossiers")
def research_dossiers(limit: int, include_archived: bool):
    """List persistent research dossiers."""
    scheduler = _get_scheduler(skip_advisor=True)
    dossiers = scheduler.list_research_dossiers(include_archived=include_archived, limit=limit)
    if not dossiers:
        console.print("[yellow]No research dossiers yet. Use 'coach research dossier-create'.[/]")
        return

    table = Table(show_header=True, title="Research Dossiers")
    table.add_column("ID", style="cyan")
    table.add_column("Topic")
    table.add_column("Status", style="green")
    table.add_column("Updated", style="dim")
    table.add_column("Latest Change")
    for dossier in dossiers:
        table.add_row(
            dossier["dossier_id"],
            dossier["topic"][:40],
            dossier.get("status", "active"),
            (dossier.get("last_updated") or "")[:10],
            (dossier.get("latest_change_summary") or "No updates yet")[:60],
        )
    console.print(table)


@research.command("dossier-create")
@click.argument("topic")
@click.option("--scope", default="", help="Optional scope for the dossier")
@click.option("--question", "core_questions", multiple=True, help="Core question to track")
@click.option("--assumption", "assumptions", multiple=True, help="Assumption to track")
@click.option("--goal", "related_goals", multiple=True, help="Related goal")
@click.option("--subtopic", "tracked_subtopics", multiple=True, help="Tracked subtopic")
def research_dossier_create(
    topic: str,
    scope: str,
    core_questions: tuple[str, ...],
    assumptions: tuple[str, ...],
    related_goals: tuple[str, ...],
    tracked_subtopics: tuple[str, ...],
):
    """Create a persistent research dossier."""
    scheduler = _get_scheduler(skip_advisor=True)
    dossier = scheduler.create_research_dossier(
        topic=topic,
        scope=scope,
        core_questions=list(core_questions),
        assumptions=list(assumptions),
        related_goals=list(related_goals),
        tracked_subtopics=list(tracked_subtopics),
    )
    if not dossier:
        console.print("[red]Failed to create dossier.[/]")
        return
    console.print(f"[green]Created dossier[/] {dossier['dossier_id']} for [cyan]{dossier['topic']}[/]")


@research.command("dossier-view")
@click.argument("dossier_id")
def research_dossier_view(dossier_id: str):
    """View a research dossier and its latest updates."""
    scheduler = _get_scheduler(skip_advisor=True)
    dossier = scheduler.get_research_dossier(dossier_id)
    if not dossier:
        console.print(f"[red]Unknown dossier:[/] {dossier_id}")
        return

    console.print(f"\n[cyan bold]{dossier['title']}[/]")
    console.print(f"[dim]Status: {dossier.get('status', 'active')}[/]")
    console.print(f"[dim]Last updated: {(dossier.get('last_updated') or 'Never')[:19]}[/]")
    console.print(f"[dim]Latest change: {dossier.get('latest_change_summary') or 'No updates yet'}[/]\n")
    console.print(Markdown(dossier.get("content", "")))

    updates = dossier.get("updates") or []
    if updates:
        console.print("\n[bold]Recent Updates[/]")
        for update in updates[:5]:
            console.print(f"- {(update.get('created') or '')[:10]}: {update.get('change_summary') or update.get('title')}")
