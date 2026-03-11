"""Profile CLI commands."""

import subprocess
import sys

import click
from rich.console import Console
from rich.table import Table

from cli.utils import get_components, get_profile_storage

console = Console()


@click.group()
def profile():
    """View and manage your professional profile."""
    pass


@profile.command("show")
def profile_show():
    """View current profile."""
    ps = get_profile_storage()
    p = ps.load()
    if not p:
        console.print(
            "[yellow]No profile found. Run [cyan]coach profile update[/] to create one.[/]"
        )
        return

    console.print(f"\n[cyan bold]{p.current_role or 'No role set'}[/] ({p.career_stage})")
    if p.location:
        console.print(f"[dim]Location: {p.location}[/]")

    if p.skills:
        table = Table(title="Skills", show_header=True)
        table.add_column("Skill")
        table.add_column("Proficiency", justify="center")
        for s in sorted(p.skills, key=lambda x: x.proficiency, reverse=True):
            bar = (
                "[green]"
                + "#" * s.proficiency
                + "[/]"
                + "[dim]"
                + "." * (5 - s.proficiency)
                + "[/]"
            )
            table.add_row(s.name, bar)
        console.print(table)

    if p.languages_frameworks:
        console.print(f"\n[bold]Languages/Frameworks:[/] {', '.join(p.languages_frameworks)}")
    if p.interests:
        console.print(f"[bold]Interests:[/] {', '.join(p.interests)}")
    if p.aspirations:
        console.print(f"\n[bold]Aspirations:[/] {p.aspirations}")

    console.print(
        f"\n[dim]Learning style: {p.learning_style} | Available: {p.weekly_hours_available}h/week[/]"
    )
    if p.updated_at:
        console.print(f"[dim]Last updated: {p.updated_at[:10]}[/]")
        if p.is_stale():
            console.print(
                "[yellow]Profile is >90 days old. Consider running [cyan]coach profile update[/][/]"
            )


@profile.command("update")
def profile_update():
    """Run the profile interview (or re-interview)."""
    c = get_components()
    ps = get_profile_storage(c["config"])

    from profile.interview import ProfileInterviewAborted, ProfileInterviewError, ProfileInterviewer

    from advisor.engine import LLMError

    interviewer = ProfileInterviewer(
        llm_caller=c["advisor"]._call_llm,
        storage=ps,
    )

    try:
        console.print("[bold]Starting profile interview...[/]\n")
        p = interviewer.run_interactive(
            output_fn=lambda t: console.print(t),
        )
        console.print(
            f"\n[green]Profile saved![/] {len(p.skills)} skills, {len(p.interests)} interests"
        )
        console.print(f"[dim]Saved to: {ps.path}[/]")
    except ProfileInterviewAborted as e:
        console.print(f"[yellow]Interview cancelled:[/] {e}")
        sys.exit(1)
    except ProfileInterviewError as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)
    except LLMError as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


@profile.command("edit")
def profile_edit():
    """Edit profile YAML in $EDITOR."""
    import os
    import yaml

    from pydantic import ValidationError

    ps = get_profile_storage()
    if not ps.exists():
        # Create default profile
        from profile.storage import UserProfile

        ps.save(UserProfile())
        console.print(f"[green]Created default profile at {ps.path}[/]")

    editor = os.environ.get("EDITOR", "vim")
    try:
        subprocess.run([editor, str(ps.path)], check=True)
        # Validate after edit
        try:
            p = ps.load()
        except (ValidationError, ValueError, TypeError, yaml.YAMLError) as e:
            console.print(f"[red]Profile validation failed:[/] {e}")
            raise SystemExit(1) from e
        if p:
            console.print(
                f"[green]Profile valid.[/] {len(p.skills)} skills, {len(p.interests)} interests"
            )
        else:
            console.print("[red]Warning: Profile YAML may be invalid.[/]")
    except subprocess.CalledProcessError:
        console.print("[red]Editor exited with error[/]")
    except FileNotFoundError:
        console.print(f"[red]Editor not found:[/] {editor}")


@profile.command("set")
@click.argument("field")
@click.argument("value")
def profile_set(field: str, value: str):
    """Set a single profile field. E.g.: coach profile set location 'San Francisco, CA'"""
    ps = get_profile_storage()
    try:
        # Parse list fields
        list_fields = {"interests", "languages_frameworks"}
        if field in list_fields:
            value = [v.strip() for v in value.split(",")]
        elif field == "skills":
            from profile.storage import Skill

            value = [Skill(name=v.strip(), proficiency=3) for v in value.split(",")]

        ps.update_field(field, value)
        console.print(f"[green]Updated {field}[/]")
    except ValueError as e:
        console.print(f"[red]{e}[/]")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
