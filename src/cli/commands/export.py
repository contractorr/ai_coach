"""Data export and backup CLI commands."""

import json
import shutil
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console

from cli.config import get_paths, load_config
from cli.utils import get_rec_db_path

console = Console()


@click.group()
def export():
    """Export and backup coach data."""
    pass


@export.command("all")
@click.option("-o", "--output", required=True, type=click.Path(), help="Output path")
@click.option(
    "-f",
    "--format",
    "fmt",
    default="zip",
    type=click.Choice(["json", "markdown", "zip"]),
    help="Export format",
)
def export_all(output: str, fmt: str):
    """Export all data (journal, intel, recommendations)."""
    config = load_config()
    paths = get_paths(config)
    output_path = Path(output)

    with console.status("Exporting..."):
        if fmt == "zip":
            _export_zip(config, paths, output_path)
        elif fmt == "json":
            _export_json(config, paths, output_path)
        elif fmt == "markdown":
            _export_markdown(config, paths, output_path)

    console.print(f"[green]Exported to {output_path}[/]")


@export.command("backup")
@click.option("-d", "--dir", "backup_dir", default="~/coach/backups", help="Backup directory")
def backup(backup_dir: str):
    """Create incremental backup snapshot."""
    config = load_config()
    paths = get_paths(config)
    backup_path = Path(backup_dir).expanduser()
    backup_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_dir = backup_path / f"backup_{timestamp}"

    with console.status("Backing up..."):
        snapshot_dir.mkdir()

        # Copy journal
        journal_dir = paths["journal_dir"]
        if journal_dir.exists():
            shutil.copytree(journal_dir, snapshot_dir / "journal")

        # Copy intel db
        intel_db = paths["intel_db"]
        if intel_db.exists():
            shutil.copy2(intel_db, snapshot_dir / "intel.db")

        # Copy recommendations
        rec_dir = get_rec_db_path(config)
        if rec_dir.exists():
            shutil.copytree(rec_dir, snapshot_dir / "recommendations")

        # Copy config
        config_path = Path.home() / "coach" / "config.yaml"
        if config_path.exists():
            shutil.copy2(config_path, snapshot_dir / "config.yaml")

        # Write manifest
        manifest = {
            "timestamp": timestamp,
            "journal_entries": len(list((snapshot_dir / "journal").glob("*.md")))
            if (snapshot_dir / "journal").exists()
            else 0,
            "has_intel_db": (snapshot_dir / "intel.db").exists(),
            "has_recommendations": (snapshot_dir / "recommendations").exists(),
        }
        (snapshot_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    console.print(f"[green]Backup saved:[/] {snapshot_dir}")
    console.print(f"  Journal: {manifest['journal_entries']} entries")
    console.print(f"  Intel DB: {'yes' if manifest['has_intel_db'] else 'no'}")
    console.print(f"  Recommendations: {'yes' if manifest['has_recommendations'] else 'no'}")


def _export_zip(config_or_paths: dict, paths_or_output, output_path: Path | None = None):
    """Export everything as a zip file."""
    import tempfile

    if output_path is None:
        config = {"paths": {"intel_db": str(config_or_paths["intel_db"])}}
        paths = config_or_paths
        output_path = paths_or_output
    else:
        config = config_or_paths
        paths = paths_or_output

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "coach_export"
        tmp_path.mkdir()

        # Journal
        journal_dir = paths["journal_dir"]
        if journal_dir.exists():
            shutil.copytree(journal_dir, tmp_path / "journal")

        # Intel
        intel_db = paths["intel_db"]
        if intel_db.exists():
            shutil.copy2(intel_db, tmp_path / "intel.db")

        # Recommendations
        rec_dir = get_rec_db_path(config)
        if rec_dir.exists():
            shutil.copytree(rec_dir, tmp_path / "recommendations")

        # Create zip
        output_stem = str(output_path).replace(".zip", "")
        shutil.make_archive(output_stem, "zip", tmp, "coach_export")


def _export_json(config_or_paths: dict, paths_or_output, output_path: Path | None = None):
    """Export journal + recommendations as JSON."""
    import frontmatter

    if output_path is None:
        config = {"paths": {"intel_db": str(config_or_paths["intel_db"])}}
        paths = config_or_paths
        output_path = paths_or_output
    else:
        config = config_or_paths
        paths = paths_or_output

    data = {"journal": [], "recommendations": []}

    journal_dir = paths["journal_dir"]
    if journal_dir.exists():
        for f in sorted(journal_dir.glob("*.md")):
            try:
                post = frontmatter.load(f)
                data["journal"].append(
                    {
                        "filename": f.name,
                        "metadata": {k: str(v) for k, v in post.metadata.items()},
                        "content": post.content,
                    }
                )
            except Exception:
                continue

    rec_dir = get_rec_db_path(config)
    if rec_dir.exists():
        for f in sorted(rec_dir.glob("*.md")):
            try:
                post = frontmatter.load(f)
                data["recommendations"].append(
                    {
                        "filename": f.name,
                        "metadata": {k: str(v) for k, v in post.metadata.items()},
                        "content": post.content,
                    }
                )
            except Exception:
                continue

    output_path.write_text(json.dumps(data, indent=2, default=str))


def _export_markdown(config_or_paths: dict, paths_or_output, output_path: Path | None = None):
    """Export as combined markdown file."""
    import frontmatter

    if output_path is None:
        config = {"paths": {"intel_db": str(config_or_paths["intel_db"])}}
        paths = config_or_paths
        output_path = paths_or_output
    else:
        config = config_or_paths
        paths = paths_or_output

    sections = []

    journal_dir = paths["journal_dir"]
    if journal_dir.exists():
        sections.append("# Journal Entries\n")
        for f in sorted(journal_dir.glob("*.md")):
            try:
                post = frontmatter.load(f)
                title = post.get("title", f.stem)
                created = post.get("created", "")[:10]
                sections.append(f"## {title} ({created})\n\n{post.content}\n\n---\n")
            except Exception:
                continue

    rec_dir = get_rec_db_path(config)
    if rec_dir.exists():
        sections.append("\n# Recommendations\n")
        for f in sorted(rec_dir.glob("*.md")):
            try:
                post = frontmatter.load(f)
                title = post.get("title", f.stem)
                sections.append(f"## {title}\n\n{post.content}\n\n---\n")
            except Exception:
                continue

    output_path.write_text("\n".join(sections))
