"""Curriculum content tooling commands."""

import json
from pathlib import Path

import click
from rich.console import Console

from curriculum.content_schema import (
    audit_curriculum_root,
    iter_curriculum_content_files,
    lint_curriculum_paths,
    migrate_curriculum_corpus,
)

console = Console()


@click.group()
def curriculum():
    """Curriculum content schema, linting, and migration tools."""
    pass


@curriculum.command("lint")
@click.option(
    "--path",
    "content_path",
    default="content/curriculum",
    show_default=True,
    type=click.Path(path_type=Path),
    help="Curriculum content root to lint.",
)
@click.option(
    "--format",
    "output_format",
    default="text",
    show_default=True,
    type=click.Choice(["text", "json"]),
    help="Output format.",
)
@click.option(
    "--fail-on-issues/--no-fail-on-issues",
    default=True,
    show_default=True,
    help="Exit non-zero when lint issues are found.",
)
def lint_curriculum(content_path: Path, output_format: str, fail_on_issues: bool):
    """Run baseline curriculum schema and reference checks."""
    files = iter_curriculum_content_files(content_path)
    report = lint_curriculum_paths(files, root=content_path)
    error_count = sum(1 for issue in report.issues if issue.severity == "error")
    warning_count = len(report.issues) - error_count

    if output_format == "json":
        console.print(json.dumps(report.model_dump(), indent=2))
    else:
        console.print(
            f"Scanned {report.documents_scanned} curriculum documents, "
            f"found {len(report.issues)} issues ({error_count} errors, {warning_count} warnings)."
        )
        for issue in report.issues:
            color = "red" if issue.severity == "error" else "yellow"
            console.print(
                f"[{color}]{issue.severity}[/{color}] {issue.code} {issue.path}: {issue.message}"
            )

    if fail_on_issues and report.issues:
        raise SystemExit(1)


@curriculum.command("migrate")
@click.option(
    "--source",
    "source_root",
    default="content/curriculum",
    show_default=True,
    type=click.Path(path_type=Path),
    help="Source curriculum root to migrate.",
)
@click.option(
    "--output",
    "output_root",
    required=True,
    type=click.Path(path_type=Path),
    help="Destination root for generated MDX curriculum files.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing generated files in the output directory.",
)
def migrate_curriculum(source_root: Path, output_root: Path, overwrite: bool):
    """Generate an MDX plus frontmatter curriculum corpus from existing markdown."""
    result = migrate_curriculum_corpus(source_root, output_root, overwrite=overwrite)
    console.print(
        f"Migrated {result.documents_migrated} documents to {result.output_root} "
        f"({result.documents_skipped} skipped)."
    )


@curriculum.command("audit")
@click.option(
    "--path",
    "content_path",
    default="content/curriculum",
    show_default=True,
    type=click.Path(path_type=Path),
    help="Curriculum content root to audit.",
)
@click.option(
    "--format",
    "output_format",
    default="text",
    show_default=True,
    type=click.Choice(["text", "json"]),
    help="Output format.",
)
def audit_curriculum(content_path: Path, output_format: str):
    """Audit thin guides and applied modules for rewrite planning."""
    report = audit_curriculum_root(content_path)

    if output_format == "json":
        console.print(json.dumps(report.model_dump(), indent=2))
        return

    console.print(f"Scanned {report.guides_scanned} curriculum guides/modules.")
    if report.superseded_aliases:
        console.print("Superseded aliases: " + ", ".join(report.superseded_aliases))

    console.print("\nTop rewrite priorities:")
    for index, guide in enumerate(report.thin_guides[:10], start=1):
        console.print(
            f"{index}. {guide.guide_id} "
            f"({guide.chapter_count} chapters, {guide.total_word_count} words) - {guide.rationale}"
        )

    console.print("\nApplied modules / capstones:")
    for guide in report.applied_modules:
        console.print(
            f"- {guide.guide_id} ({guide.total_word_count} words)"
            + (f" -> programs: {', '.join(guide.program_ids)}" if guide.program_ids else "")
        )
