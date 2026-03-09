"""Advisor CLI commands."""

import sys

import click
from rich.console import Console
from rich.markdown import Markdown

from advisor.engine import LLMError
from cli.utils import get_components
from services.advice import run_advice
from services.daily_brief import build_daily_brief, collect_daily_brief_inputs

console = Console()


@click.command()
def today():
    """Show today's prioritized action plan (no LLM needed)."""

    from rich.table import Table

    from cli.utils import get_profile_storage, get_recommendation_storage

    c = get_components(skip_advisor=True)

    brief_inputs = collect_daily_brief_inputs(
        c["storage"],
        profile_storage=get_profile_storage(c["config"], storage_paths=c.get("storage_paths")),
        recommendation_storage=get_recommendation_storage(
            c["config"],
            storage_paths=c.get("storage_paths"),
        ),
    )
    brief = build_daily_brief(**brief_inputs)

    if not brief.items:
        console.print("[yellow]Nothing for today.[/]")
        return

    table = Table(
        title=f"Today's Focus ({brief.used_minutes}/{brief.budget_minutes} min)", show_header=True
    )
    table.add_column("#", style="bold", width=3)
    table.add_column("Type", style="cyan", width=14)
    table.add_column("Title")
    table.add_column("Time", justify="right", width=6)

    for item in brief.items:
        table.add_row(
            str(item.priority),
            item.kind,
            item.title,
            f"{item.time_minutes}m",
        )

    console.print(table)
    if brief.used_minutes > brief.budget_minutes:
        console.print("[yellow]Over budget — consider trimming.[/]")


@click.command()
@click.argument("question")
@click.option(
    "--type",
    "advice_type",
    default="general",
    type=click.Choice(["general", "career", "goals", "opportunities", "skill_gap"]),
    help="Type of advice to get",
)
def ask(question: str, advice_type: str):
    """Ask a question and get contextual advice."""
    c = get_components()

    try:
        with console.status("Thinking..."):
            result = run_advice(c["advisor"], question, advice_type=advice_type)
        console.print()
        console.print(Markdown(result["answer"]))
    except LLMError as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


@click.command()
def review():
    """Generate weekly review from recent entries."""
    c = get_components()

    try:
        with console.status("Generating weekly review..."):
            response = c["advisor"].weekly_review()
        console.print()
        console.print(Markdown(response))
    except LLMError as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


@click.command()
def opportunities():
    """Detect opportunities based on your profile and trends."""
    c = get_components()

    try:
        with console.status("Analyzing opportunities..."):
            response = c["advisor"].detect_opportunities()
        console.print()
        console.print(Markdown(response))
    except LLMError as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


@click.group()
def goals():
    """Goal tracking, check-ins, and analysis."""
    from cli.utils import warn_experimental

    warn_experimental("Goal tracking")


@goals.command("analyze")
@click.argument("goal", required=False)
def goals_analyze(goal: str):
    """Analyze goal progress with AI. Optionally specify a goal to focus on."""
    c = get_components()

    try:
        with console.status("Analyzing goals..."):
            response = c["advisor"].analyze_goals(specific_goal=goal)
        console.print()
        console.print(Markdown(response))
    except LLMError as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


@goals.command("list")
@click.option("-a", "--all", "show_all", is_flag=True, help="Include completed/abandoned")
@click.option("-s", "--stale", is_flag=True, help="Show only stale goals")
def goals_list(show_all: bool, stale: bool):
    """List goals with staleness indicator."""
    from pathlib import Path

    from rich.table import Table

    from advisor.goals import GoalTracker

    c = get_components(skip_advisor=True)
    tracker = GoalTracker(c["storage"])

    if stale:
        goal_list = tracker.get_stale_goals()
    else:
        goal_list = tracker.get_goals(include_inactive=show_all)

    if not goal_list:
        console.print("[yellow]No goals found.[/]")
        return

    table = Table(show_header=True)
    table.add_column("Path", style="dim", max_width=30)
    table.add_column("Title")
    table.add_column("Status", style="cyan")
    table.add_column("Last Check", justify="right")
    table.add_column("Stale", justify="center")

    for g in goal_list:
        path_short = Path(g["path"]).name[:28]
        last = g.get("last_checked", "")[:10] if g.get("last_checked") else "never"
        days = g.get("days_since_check")
        days_str = f"{last} ({days}d)" if days else last

        stale_indicator = "[red]![/]" if g["is_stale"] else ""

        table.add_row(
            path_short,
            g["title"][:40],
            g["status"],
            days_str,
            stale_indicator,
        )

    console.print(table)

    stale_count = sum(1 for g in goal_list if g["is_stale"])
    if stale_count:
        console.print(f"\n[yellow]{stale_count} goal(s) need check-in[/]")


@goals.command("check-in")
@click.argument("goal_path", type=click.Path(exists=True))
@click.option("-n", "--notes", help="Check-in notes")
def goals_checkin(goal_path: str, notes: str):
    """Record a check-in for a goal."""
    from pathlib import Path

    from advisor.goals import GoalTracker

    c = get_components(skip_advisor=True)
    tracker = GoalTracker(c["storage"])

    if tracker.check_in_goal(Path(goal_path), notes):
        console.print("[green]Checked in on goal![/]")
        if notes:
            console.print(f"[dim]Notes: {notes}[/]")
    else:
        console.print("[red]Failed to check in on goal[/]")


@goals.command("status")
@click.argument("goal_path", type=click.Path(exists=True))
@click.option(
    "-s",
    "--status",
    required=True,
    type=click.Choice(["active", "paused", "completed", "abandoned"]),
    help="New status",
)
def goals_status(goal_path: str, status: str):
    """Update goal status."""
    from pathlib import Path

    from advisor.goals import GoalTracker

    c = get_components(skip_advisor=True)
    tracker = GoalTracker(c["storage"])

    if tracker.update_goal_status(Path(goal_path), status):
        console.print(f"[green]Updated goal status to: {status}[/]")
    else:
        console.print("[red]Failed to update goal status[/]")


@goals.command("add")
@click.option("-t", "--title", required=True, help="Goal title")
@click.option("-d", "--description", help="Goal description")
@click.option("--check-days", default=14, help="Days between check-ins")
def goals_add(title: str, description: str, check_days: int):
    """Create a new goal entry."""
    from advisor.goals import get_goal_defaults

    c = get_components(skip_advisor=True)

    content = description or f"# {title}\n\nGoal created."
    metadata = get_goal_defaults()
    metadata["check_in_days"] = check_days

    filepath = c["storage"].create(
        content=content,
        entry_type="goal",
        title=title,
        metadata=metadata,
    )

    console.print(f"[green]Created goal:[/] {filepath.name}")


@goals.group("milestone")
def goals_milestone():
    """Manage goal milestones."""
    pass


@goals_milestone.command("add")
@click.argument("goal_path", type=click.Path(exists=True))
@click.argument("title")
def milestone_add(goal_path: str, title: str):
    """Add a milestone to a goal."""
    from pathlib import Path

    from advisor.goals import GoalTracker

    c = get_components(skip_advisor=True)
    tracker = GoalTracker(c["storage"])

    if tracker.add_milestone(Path(goal_path), title):
        console.print(f"[green]Added milestone:[/] {title}")
    else:
        console.print("[red]Failed to add milestone[/]")


@goals_milestone.command("complete")
@click.argument("goal_path", type=click.Path(exists=True))
@click.argument("index", type=int)
def milestone_complete(goal_path: str, index: int):
    """Complete a milestone by index (0-based)."""
    from pathlib import Path

    from advisor.goals import GoalTracker

    c = get_components(skip_advisor=True)
    tracker = GoalTracker(c["storage"])

    if tracker.complete_milestone(Path(goal_path), index):
        progress = tracker.get_progress(Path(goal_path))
        console.print(f"[green]Milestone completed![/] Progress: {progress['percent']}%")
    else:
        console.print("[red]Failed to complete milestone[/]")


@goals.command("progress")
@click.argument("goal_path", type=click.Path(exists=True))
def goals_progress(goal_path: str):
    """Show progress bar and milestone list for a goal."""
    from pathlib import Path

    from rich.progress import BarColumn, Progress, TextColumn
    from rich.table import Table

    from advisor.goals import GoalTracker

    c = get_components(skip_advisor=True)
    tracker = GoalTracker(c["storage"])
    progress = tracker.get_progress(Path(goal_path))

    # Progress bar
    console.print(
        f"\n[bold]Progress: {progress['percent']}%[/] ({progress['completed']}/{progress['total']} milestones)"
    )

    with Progress(
        TextColumn("[bold]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("{task.percentage:.0f}%"),
        console=console,
    ) as bar:
        bar.add_task("Progress", total=100, completed=progress["percent"])

    # Milestone list
    if progress["milestones"]:
        table = Table(show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Milestone")
        table.add_column("Status", justify="center")
        table.add_column("Completed At", style="dim")

        for i, m in enumerate(progress["milestones"]):
            status = "[green]Done[/]" if m.get("completed") else "[yellow]Pending[/]"
            completed_at = (m.get("completed_at") or "")[:10]
            table.add_row(str(i), m.get("title", ""), status, completed_at)

        console.print(table)
    else:
        console.print(
            '[dim]No milestones yet. Add with: coach goals milestone add <path> "title"[/]'
        )
