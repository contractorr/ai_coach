"""Recommendation CLI commands."""

import sys

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from advisor.engine import LLMError
from cli.utils import get_components, get_rec_db_path, get_recommendation_storage
from services.recommendation_actions import (
    build_weekly_plan as build_weekly_action_plan,
)
from services.recommendation_actions import (
    create_action_item as create_tracked_action,
)
from services.recommendation_actions import (
    list_action_items as list_tracked_actions,
)
from services.recommendation_actions import (
    update_action_item as update_tracked_action,
)

console = Console()

CATEGORIES = ["learning", "career", "entrepreneurial", "investment", "events", "projects"]
ACTION_ITEM_STATUSES = ["accepted", "deferred", "blocked", "completed", "abandoned"]
ACTION_ITEM_EFFORTS = ["small", "medium", "large"]
ACTION_ITEM_DUE_WINDOWS = ["today", "this_week", "later"]


def _get_storage():
    c = get_components(skip_advisor=True)
    return get_recommendation_storage(c["config"], storage_paths=c.get("storage_paths"))


def _display_action_item(action: dict):
    console.print(f"[cyan bold]{action['recommendation_title']}[/] [dim][{action['category']}][/]")
    item = action["action_item"]
    console.print(
        f"[dim]Status: {item['status']} | Effort: {item['effort']} | Window: {item['due_window']}[/]"
    )
    console.print(f"[bold]Objective:[/] {item['objective']}")
    console.print(f"[bold]Next step:[/] {item['next_step']}")
    if item.get("success_criteria"):
        console.print(f"[bold]Success:[/] {item['success_criteria']}")
    if item.get("goal_title"):
        console.print(f"[dim]Goal: {item['goal_title']}[/]")
    if item.get("review_notes"):
        console.print(f"[dim]Review notes: {item['review_notes']}[/]")
    console.print()


def _display_recommendations(recs: list):
    """Display recommendations in formatted output."""
    if not recs:
        console.print("[yellow]No recommendations generated (may need more journal context).[/]")
        return

    for rec in recs:
        console.print(f"\n[cyan bold]{rec.title}[/] [dim][{rec.category}][/]")
        console.print(f"[green]Score: {rec.score:.1f}[/]")
        if rec.description:
            console.print(rec.description)
        if rec.rationale:
            console.print(f"\n[dim]Why: {rec.rationale}[/]")
        console.print()


@click.group()
def recommend():
    """Proactive recommendations for learning, career, entrepreneurial, and investment opportunities."""
    pass


@recommend.command("generate")
@click.option(
    "-c",
    "--category",
    type=click.Choice(CATEGORIES + ["all"]),
    default="all",
    help="Category to generate",
)
@click.option("-n", "--limit", default=3, help="Max recommendations per category")
def recommend_generate(category: str, limit: int):
    """Generate recommendations."""
    c = get_components()
    rec_config = c["config"].get("recommendations", {})
    rec_path = get_rec_db_path(c["config"])

    try:
        with console.status(f"Generating {category} recommendations..."):
            recs = c["advisor"].generate_recommendations(
                category, rec_path, rec_config, max_items=limit
            )
        _display_recommendations(recs)
    except LLMError as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


@recommend.command("brief")
@click.option("-n", "--limit", default=5, help="Max items in brief")
@click.option("--save", is_flag=True, help="Save as journal entry")
def recommend_brief(limit: int, save: bool):
    """Generate weekly action brief."""
    c = get_components()
    rec_config = c["config"].get("recommendations", {})
    rec_path = get_rec_db_path(c["config"])
    min_score = rec_config.get("scoring", {}).get("min_threshold", 6.0)

    try:
        with console.status("Generating action brief..."):
            brief = c["advisor"].generate_action_brief(
                rec_path,
                journal_storage=c["storage"] if save else None,
                max_items=limit,
                min_score=min_score,
                save=save,
            )
        console.print()
        console.print(Markdown(brief))
        if save:
            console.print("\n[green]Saved to journal as action_brief entry.[/]")
    except LLMError as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


@recommend.command("history")
@click.option("-n", "--limit", default=20, help="Max entries")
@click.option("-c", "--category", help="Filter by category")
@click.option("-s", "--status", help="Filter by status")
def recommend_history(limit: int, category: str, status: str):
    """View recommendation history."""
    c = get_components(skip_advisor=True)
    storage = get_recommendation_storage(c["config"], storage_paths=c.get("storage_paths"))

    if category:
        recs = storage.list_by_category(category, status=status, limit=limit)
    else:
        recs = storage.list_recent(days=90, status=status, limit=limit)

    if not recs:
        console.print("[yellow]No recommendations found.[/]")
        return

    table = Table(show_header=True)
    table.add_column("ID", style="dim")
    table.add_column("Category", style="cyan")
    table.add_column("Title")
    table.add_column("Score", justify="right")
    table.add_column("Status", style="green")
    table.add_column("Date", style="dim")

    for rec in recs:
        date = rec.created_at[:10] if rec.created_at else "?"
        table.add_row(
            str(rec.id),
            rec.category,
            rec.title[:40],
            f"{rec.score:.1f}",
            rec.status,
            date,
        )

    console.print(table)


@recommend.group("action")
def recommend_action():
    """Track recommendation execution as lightweight action items."""
    pass


@recommend_action.command("create")
@click.argument("rec_id", type=str)
@click.option("--goal-path", type=str, help="Optional goal path to attach")
@click.option("--goal-title", type=str, help="Optional goal title to show in CLI")
@click.option("--effort", type=click.Choice(ACTION_ITEM_EFFORTS), help="Effort estimate")
@click.option(
    "--due-window",
    type=click.Choice(ACTION_ITEM_DUE_WINDOWS),
    help="Prioritization bucket",
)
def recommend_action_create(
    rec_id: str,
    goal_path: str | None,
    goal_title: str | None,
    effort: str | None,
    due_window: str | None,
):
    """Convert a recommendation into a tracked action item."""
    storage = _get_storage()
    result = create_tracked_action(
        storage,
        rec_id,
        goal_path=goal_path,
        goal_title=goal_title,
        effort=effort,
        due_window=due_window,
    )
    if not result["success"]:
        console.print(f"[red]Recommendation {rec_id} not found[/]")
        return

    record = result["record"]
    if not result["persisted"] or not record:
        console.print(f"[red]Failed to load tracked action for {rec_id}[/]")
        return

    console.print(f"[green]Tracked action created for recommendation {rec_id}[/]")
    _display_action_item(
        {
            "recommendation_title": record["recommendation_title"],
            "category": record["category"],
            "action_item": record["action_item"],
        }
    )


@recommend_action.command("list")
@click.option("-n", "--limit", default=20, help="Max actions")
@click.option("--status", type=click.Choice(ACTION_ITEM_STATUSES), help="Filter by action status")
@click.option("--goal-path", type=str, help="Filter by linked goal path")
def recommend_action_list(limit: int, status: str | None, goal_path: str | None):
    """List tracked recommendation action items."""
    storage = _get_storage()
    result = list_tracked_actions(storage, status=status, goal_path=goal_path, limit=limit)
    actions = result["actions"]
    if not actions:
        console.print("[yellow]No tracked actions found.[/]")
        return

    table = Table(show_header=True)
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Status", style="green")
    table.add_column("Effort")
    table.add_column("Window")
    table.add_column("Goal", style="dim")

    for action in actions:
        item = action["action_item"]
        table.add_row(
            action["recommendation_id"],
            action["recommendation_title"][:42],
            item.get("status", ""),
            item.get("effort", ""),
            item.get("due_window", ""),
            item.get("goal_title") or "",
        )

    console.print(table)


@recommend_action.command("update")
@click.argument("rec_id", type=str)
@click.option("--status", type=click.Choice(ACTION_ITEM_STATUSES), help="New action status")
@click.option("--effort", type=click.Choice(ACTION_ITEM_EFFORTS), help="New effort estimate")
@click.option(
    "--due-window",
    type=click.Choice(ACTION_ITEM_DUE_WINDOWS),
    help="New prioritization bucket",
)
@click.option("--review-notes", type=str, help="Review notes or outcome summary")
def recommend_action_update(
    rec_id: str,
    status: str | None,
    effort: str | None,
    due_window: str | None,
    review_notes: str | None,
):
    """Update a tracked action item."""
    storage = _get_storage()
    result = update_tracked_action(
        storage,
        rec_id,
        status=status,
        effort=effort,
        due_window=due_window,
        review_notes=review_notes,
    )
    if not result["success"]:
        console.print(f"[red]Tracked action for recommendation {rec_id} not found[/]")
        return

    record = result["record"]
    console.print(f"[green]Updated tracked action for recommendation {rec_id}[/]")
    if record:
        _display_action_item(
            {
                "recommendation_title": record["recommendation_title"],
                "category": record["category"],
                "action_item": record["action_item"],
            }
        )


@recommend_action.command("weekly-plan")
@click.option("--capacity", default=6, help="Weekly capacity points")
@click.option("--goal-path", type=str, help="Optional goal path filter")
def recommend_action_weekly_plan(capacity: int, goal_path: str | None):
    """Assemble a weekly plan from accepted tracked actions."""
    storage = _get_storage()
    plan = build_weekly_action_plan(storage, capacity_points=capacity, goal_path=goal_path)
    console.print(
        f"[cyan bold]Weekly plan[/] [dim]({plan['used_points']}/{plan['capacity_points']} points used)[/]"
    )
    if not plan["items"]:
        console.print("[yellow]No accepted actions fit the current capacity.[/]")
        return

    for action in plan["items"]:
        _display_action_item(
            {
                "recommendation_title": action["recommendation_title"],
                "category": action["category"],
                "action_item": action["action_item"],
            }
        )


@recommend.command("update")
@click.argument("rec_id", type=str)
@click.option(
    "--status",
    "-s",
    required=True,
    type=click.Choice(["suggested", "in_progress", "completed", "dismissed"]),
    help="New status",
)
def recommend_update(rec_id: str, status: str):
    """Update recommendation status."""
    c = get_components(skip_advisor=True)
    storage = get_recommendation_storage(c["config"], storage_paths=c.get("storage_paths"))

    if storage.update_status(rec_id, status):
        console.print(f"[green]Updated recommendation {rec_id} to {status}[/]")
    else:
        console.print(f"[red]Recommendation {rec_id} not found[/]")


@recommend.command("view")
@click.argument("rec_id", type=str)
def recommend_view(rec_id: str):
    """View a specific recommendation."""
    c = get_components(skip_advisor=True)
    storage = get_recommendation_storage(c["config"], storage_paths=c.get("storage_paths"))

    rec = storage.get(rec_id)
    if not rec:
        console.print(f"[red]Recommendation {rec_id} not found[/]")
        return

    console.print(f"\n[cyan bold]{rec.title}[/]")
    console.print(
        f"[dim]Category: {rec.category} | Score: {rec.score:.1f} | Status: {rec.status}[/]"
    )
    console.print(f"[dim]Created: {rec.created_at[:10] if rec.created_at else '?'}[/]")

    if rec.metadata and rec.metadata.get("user_rating"):
        rating = rec.metadata["user_rating"]
        stars = "★" * rating + "☆" * (5 - rating)
        console.print(f"[yellow]Rating: {stars}[/]")

    console.print()
    if rec.description:
        console.print(f"[bold]Description:[/] {rec.description}")
    if rec.rationale:
        console.print(f"\n[bold]Rationale:[/] {rec.rationale}")

    if rec.metadata and rec.metadata.get("action_plan"):
        console.print("\n[bold green]Action Plan:[/]")
        console.print(Markdown(rec.metadata["action_plan"]))

    if rec.metadata and rec.metadata.get("feedback_comment"):
        console.print(f"\n[dim]Your feedback: {rec.metadata['feedback_comment']}[/]")


@recommend.command("rate")
@click.argument("rec_id", type=str)
@click.option("-r", "--rating", type=click.IntRange(1, 5), required=True, help="Rating 1-5")
@click.option("-c", "--comment", help="Optional feedback comment")
def recommend_rate(rec_id: str, rating: int, comment: str):
    """Rate a recommendation's usefulness."""
    c = get_components(skip_advisor=True)
    storage = get_recommendation_storage(c["config"], storage_paths=c.get("storage_paths"))

    if storage.add_feedback(rec_id, rating, comment):
        stars = "★" * rating + "☆" * (5 - rating)
        console.print(f"[green]Rated recommendation {rec_id}: {stars}[/]")
        if comment:
            console.print(f"[dim]Comment: {comment}[/]")
    else:
        console.print(f"[red]Recommendation {rec_id} not found[/]")


@recommend.command("events")
@click.option("-n", "--limit", default=10, help="Max events to show")
@click.option("--days", default=90, help="Lookback/forward window in days")
def recommend_events(limit: int, days: int):
    """Show upcoming events sorted by relevance and deadline."""
    from advisor.events import get_upcoming_events
    from cli.utils import get_profile_storage

    c = get_components(skip_advisor=True)
    ps = get_profile_storage(c["config"])
    profile = ps.load()

    events = get_upcoming_events(
        c["intel_storage"],
        profile=profile,
        days=days,
        limit=limit,
    )

    if not events:
        console.print(
            "[yellow]No upcoming events found. Run [cyan]coach scrape[/] to fetch events.[/]"
        )
        return

    from rich.table import Table

    table = Table(title="Upcoming Events", show_header=True)
    table.add_column("Score", justify="right", style="green")
    table.add_column("Event")
    table.add_column("Date", style="cyan")
    table.add_column("Location", style="dim")
    table.add_column("CFP Deadline", style="yellow")

    for e in events:
        meta = e.get("_metadata", {})
        score = f"{e['_score']:.1f}"
        date = meta.get("event_date", "?")[:10]
        location = meta.get("location", "")
        if meta.get("online"):
            location = "Online" + (f" + {location}" if location else "")
        cfp = meta.get("cfp_deadline", "")[:10] if meta.get("cfp_deadline") else ""
        table.add_row(score, e["title"][:45], date, location[:25], cfp)

    console.print(table)
