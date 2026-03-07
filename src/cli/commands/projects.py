"""Project discovery CLI commands."""

import sys

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from cli.utils import get_components, get_profile_storage
from services.projects import (
    discover_matching_project_issues,
    generate_project_ideas,
    list_project_issues,
)

console = Console()


@click.group()
def projects():
    """Discover open-source contributions and side-project ideas."""
    pass


@projects.command("discover")
@click.option("-n", "--limit", default=15, help="Max issues to show")
@click.option("--days", default=14, help="Lookback window in days")
def projects_discover(limit: int, days: int):
    """Find matching open-source issues based on your skills."""
    c = get_components(skip_advisor=True)
    ps = get_profile_storage(c["config"])
    profile = ps.load()

    payload = discover_matching_project_issues(c["intel_storage"], profile=profile, limit=limit, days=days)
    issues = payload["issues"]

    if not issues:
        console.print("[yellow]No matching issues found. Run [cyan]coach scrape[/] first.[/]")
        return

    table = Table(title="Matching Open-Source Issues", show_header=True)
    table.add_column("Match", justify="right", style="green")
    table.add_column("Issue")
    table.add_column("Repo", style="cyan")
    table.add_column("Labels", style="dim")

    for issue in issues:
        match_score = issue.get("match_score", 0)
        title = issue.get("title", "")[:45]
        # Extract repo from summary
        summary = issue.get("summary", "")
        repo = ""
        if "Repo: " in summary:
            repo = summary.split("Repo: ")[1].split(" |")[0][:30]
        tags = ", ".join(issue.get("tags", [])[:3])

        table.add_row(str(match_score), title, repo, tags[:30])

    console.print(table)
    console.print(
        f"\n[dim]Showing {len(issues)} issues. Set up profile ([cyan]coach profile update[/]) for better matching.[/]"
    )


@projects.command("ideas")
def projects_ideas():
    """Generate side-project ideas from your journal entries."""
    from advisor.engine import LLMError

    c = get_components()

    try:
        with console.status("Generating project ideas from your journal..."):
            ideas = generate_project_ideas(c["rag"], c["advisor"]._call_llm)
        console.print()
        console.print(Markdown(ideas))
    except LLMError as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


@projects.command("list")
@click.option("--days", default=14, help="Lookback window")
def projects_list(days: int):
    """List tracked project opportunities from intelligence."""
    c = get_components(skip_advisor=True)
    payload = list_project_issues(c["intel_storage"], days=days, limit=50)
    issues = payload["issues"]

    if not issues:
        console.print(
            "[yellow]No project opportunities tracked. Enable github_issues scraper in config.[/]"
        )
        return

    for issue in issues[:20]:
        console.print(f"\n[cyan]{issue['title'][:60]}[/]")
        console.print(f"[dim]{issue['summary'][:100]}[/]")
        if issue.get("url"):
            console.print(f"[blue underline]{issue['url']}[/]")
