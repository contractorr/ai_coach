"""Init CLI command."""

from pathlib import Path

import click
import yaml
from rich.console import Console

from cli.config import get_paths, load_config

console = Console()

SAMPLE_ENTRIES = [
    {
        "type": "daily",
        "title": "Getting Started with AI Coach",
        "tags": ["onboarding"],
        "content": """Today I set up AI Coach. I'm excited to start using it for personal development tracking.

My main goals right now:
- Improve my technical skills
- Be more intentional about career decisions
- Build a regular reflection habit

Looking forward to seeing how the AI coaching helps with these goals.""",
    },
    {
        "type": "goal",
        "title": "Build Consistent Journaling Habit",
        "tags": ["habits", "self-improvement"],
        "content": """I want to write journal entries at least 3 times per week.

## Why this matters
Regular reflection helps me notice patterns, make better decisions, and track progress on my goals.

## Success criteria
- 3+ entries per week for 4 consecutive weeks
- Mix of daily reflections and goal updates""",
    },
]

MINIMAL_CONFIG = {
    "llm": {
        "provider": "auto",
    },
    "paths": {
        "journal_dir": "~/coach/journal",
        "chroma_dir": "~/coach/chroma",
        "intel_db": "~/coach/intel.db",
    },
    "sources": {
        "enabled": ["hn_top", "rss_feeds"],
        "rss_feeds": [
            "https://news.ycombinator.com/rss",
            "https://feeds.arstechnica.com/arstechnica/index",
        ],
    },
}


@click.command()
@click.option("--samples", is_flag=True, help="Create sample journal entries for demo/onboarding")
def init(samples: bool):
    """Initialize coach directories, config, and optionally sample data."""
    config = load_config()
    paths = get_paths(config)

    for name, path in paths.items():
        if name in ("intel_db", "log_file"):
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/] {name}: {path}")

    # Create recommendations directory
    rec_dir = paths["intel_db"].parent / "recommendations"
    rec_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/] recommendations: {rec_dir}")

    # Create default config if not exists
    config_path = Path.home() / "coach" / "config.yaml"
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(MINIMAL_CONFIG, f, default_flow_style=False)
        console.print(f"[green]✓[/] Created config: {config_path}")

    # Create sample entries
    if samples:
        from journal.storage import JournalStorage

        storage = JournalStorage(paths["journal_dir"])
        for entry in SAMPLE_ENTRIES:
            filepath = storage.create(
                content=entry["content"],
                entry_type=entry["type"],
                title=entry["title"],
                tags=entry["tags"],
            )
            console.print(f"[green]✓[/] Sample: {filepath.name}")

    # Create profile directory
    profile_path = Path(config.get("profile", {}).get("path", "~/coach/profile.yaml")).expanduser()
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/] profile dir: {profile_path.parent}")

    console.print("\n[bold]Minimal setup:[/]")
    console.print("  1. Set ANTHROPIC_API_KEY (or OPENAI_API_KEY / GEMINI_API_KEY)")
    console.print("  2. Run [cyan]coach profile update[/] to set up your profile")
    console.print("  3. Run [cyan]coach journal add[/] to start journaling")
    console.print("  4. Run [cyan]coach ask 'What should I focus on?'[/]")
    console.print("\n[dim]Free features: HN + RSS scrapers, journal, goals, trends, events[/]")
    console.print("[dim]Paid features (optional): research (needs TAVILY_API_KEY)[/]")
