"""Tests for curriculum content schema parsing, linting, and migration."""

from curriculum.content_schema import (
    audit_curriculum_root,
    iter_curriculum_content_files,
    lint_curriculum_paths,
    load_curriculum_document,
    migrate_curriculum_corpus,
    resolve_chapter_content_path,
)


def test_load_curriculum_document_from_mdx_frontmatter(tmp_path):
    chapter = tmp_path / "01-introduction.mdx"
    chapter.write_text(
        """---
schema_version: 1
title: Introduction to Philosophy
summary: A short introduction.
objectives:
  - Understand the scope of philosophy.
checkpoints:
  - Explain why philosophy matters.
references:
  - curriculum:01-philosophy-guide/02-logic
content_format: mdx
---

# Introduction to Philosophy

Body text.
""",
        encoding="utf-8",
    )

    document = load_curriculum_document(chapter)

    assert document.has_frontmatter
    assert document.title == "Introduction to Philosophy"
    assert document.summary == "A short introduction."
    assert document.objectives == ["Understand the scope of philosophy."]
    assert document.checkpoints == ["Explain why philosophy matters."]
    assert document.content_references == ["curriculum:01-philosophy-guide/02-logic"]
    assert document.content_format == "mdx"
    assert document.schema_version == 1
    assert "schema_version" in document.frontmatter_keys


def test_load_curriculum_document_infers_legacy_metadata(tmp_path):
    chapter = tmp_path / "03-logic.md"
    chapter.write_text(
        """# Logic

## Overview

Logic studies valid reasoning.

## Deduction

Deduction content.

## Induction

Induction content.
""",
        encoding="utf-8",
    )

    document = load_curriculum_document(chapter)

    assert not document.has_frontmatter
    assert document.title == "Logic"
    assert document.summary == "Logic studies valid reasoning."
    assert document.objectives
    assert document.checkpoints
    assert document.content_format == "markdown"
    assert document.schema_version == 0


def test_lint_curriculum_paths_flags_missing_schema_fields_and_broken_refs(tmp_path):
    guide_dir = tmp_path / "01-philosophy-guide"
    guide_dir.mkdir()
    chapter = guide_dir / "01-introduction.mdx"
    chapter.write_text(
        """---
title: Introduction to Philosophy
---

# Introduction to Philosophy

See [next](./02-logic.mdx) and [missing](./03-missing.mdx).
""",
        encoding="utf-8",
    )
    referenced = guide_dir / "02-logic.mdx"
    referenced.write_text(
        """---
title: Logic
summary: Logic basics.
objectives:
  - Learn logic.
checkpoints:
  - Explain a syllogism.
---

# Logic
""",
        encoding="utf-8",
    )

    report = lint_curriculum_paths(iter_curriculum_content_files(guide_dir))
    codes = [issue.code for issue in report.issues]
    messages = [issue.message for issue in report.issues]

    assert report.documents_scanned == 2
    assert "missing_metadata" in codes
    assert "missing_objectives" in codes
    assert "missing_checkpoints" in codes
    assert any("03-missing.mdx" in message for message in messages)


def test_lint_curriculum_paths_flags_thin_chapters_path_gaps_and_manifest_issues(tmp_path):
    root = tmp_path / "content"

    core = root / "01-core-guide"
    core.mkdir(parents=True)
    (core / "01-introduction.mdx").write_text(
        """---
title: Introduction
summary: Intro summary.
objectives:
  - Learn the basics.
checkpoints:
  - Explain the basics.
---

# Introduction

""" + ("word " * 140),
        encoding="utf-8",
    )
    (core / "03-dup-a.mdx").write_text(
        """---
title: Repeated Concept
summary: First repetition.
objectives:
  - Compare two ideas.
checkpoints:
  - Explain the difference.
---

# Repeated Concept

""" + ("word " * 80),
        encoding="utf-8",
    )
    (core / "04-dup-b.mdx").write_text(
        """---
title: Repeated Concept
summary: Second repetition.
objectives:
  - Compare another angle.
checkpoints:
  - Explain another angle.
---

# Repeated Concept

""" + ("word " * 90),
        encoding="utf-8",
    )

    cyclic = root / "03-cyclic-guide"
    cyclic.mkdir()
    (cyclic / "01-start.mdx").write_text(
        """---
title: Cycle Start
summary: Start summary.
objectives:
  - Start here.
checkpoints:
  - Recall the start.
---

# Cycle Start

""" + ("word " * 130),
        encoding="utf-8",
    )

    orphan = root / "04-untracked-guide"
    orphan.mkdir()
    (orphan / "01-overview.mdx").write_text(
        """---
title: Overview
summary: Orphan summary.
objectives:
  - Understand the orphan guide.
checkpoints:
  - Explain the orphan guide.
---

# Overview

""" + ("word " * 130),
        encoding="utf-8",
    )

    (root / "skill_tree.yaml").write_text(
        """version: 1
guide_aliases:
  "00-legacy-guide": "01-core-guide"
  "00-missing-guide": "99-not-real-guide"
tracks:
      foundations:
        title: Foundations
        guides:
          - id: "01-core-guide"
            prerequisites: ["03-cyclic-guide"]
          - id: "03-cyclic-guide"
            prerequisites: ["01-core-guide", "88-missing-prereq"]
          - id: "02-missing-guide"
            prerequisites: ["00-legacy-guide", "88-missing-prereq"]
programs:
  - id: "starter"
    guides:
      - "01-core-guide"
    applied_modules:
      - "industry-missing"
""",
        encoding="utf-8",
    )

    report = lint_curriculum_paths(iter_curriculum_content_files(root), root=root)
    codes = [issue.code for issue in report.issues]

    assert "thin_chapter" in codes
    assert "path_gap" in codes
    assert "duplicate_concept" in codes
    assert "unknown_guide_alias_target" in codes
    assert "unknown_manifest_guide" in codes
    assert "unknown_prerequisite" in codes
    assert "missing_track_assignment" in codes
    assert "unknown_program_reference" in codes
    assert "prerequisite_cycle" in codes


def test_migrate_curriculum_corpus_generates_mdx_and_copies_manifest(tmp_path):
    source = tmp_path / "source"
    output = tmp_path / "output"
    guide_dir = source / "01-philosophy-guide"
    guide_dir.mkdir(parents=True)
    (guide_dir / "01-introduction.md").write_text(
        "# Introduction to Philosophy\n\n## Overview\n\nA summary paragraph.\n",
        encoding="utf-8",
    )
    (source / "skill_tree.yaml").write_text("version: 1\ntracks: {}\n", encoding="utf-8")

    result = migrate_curriculum_corpus(source, output)

    migrated = output / "01-philosophy-guide" / "01-introduction.mdx"
    assert result.documents_migrated == 1
    assert migrated.is_file()
    text = migrated.read_text(encoding="utf-8")
    assert "schema_version: 1" in text
    assert "objectives:" in text
    assert "checkpoints:" in text
    assert (output / "skill_tree.yaml").is_file()


def test_resolve_chapter_content_path_prefers_mdx(tmp_path):
    root = tmp_path / "content"
    guide_dir = root / "01-philosophy-guide"
    guide_dir.mkdir(parents=True)
    (guide_dir / "01-introduction.md").write_text("# Legacy", encoding="utf-8")
    (guide_dir / "01-introduction.mdx").write_text("# New", encoding="utf-8")

    resolved = resolve_chapter_content_path([root], "01-philosophy-guide/01-introduction")

    assert resolved == guide_dir / "01-introduction.mdx"


def test_iter_curriculum_content_files_prefers_mdx_when_both_exist(tmp_path):
    guide_dir = tmp_path / "01-philosophy-guide"
    guide_dir.mkdir()
    (guide_dir / "01-introduction.md").write_text("# Old", encoding="utf-8")
    (guide_dir / "01-introduction.mdx").write_text("# New", encoding="utf-8")

    paths = iter_curriculum_content_files(tmp_path)

    assert paths == [guide_dir / "01-introduction.mdx"]


def test_audit_curriculum_root_ranks_thin_guides_and_capstones(tmp_path):
    root = tmp_path / "content"
    guide_dir = root / "01-core-guide"
    guide_dir.mkdir(parents=True)
    (guide_dir / "01-introduction.md").write_text("# Intro\n\nShort body.\n", encoding="utf-8")

    guide_dir2 = root / "02-foundation-guide"
    guide_dir2.mkdir()
    (guide_dir2 / "01-introduction.md").write_text("# Intro\n\n" + ("word " * 3000), encoding="utf-8")
    (guide_dir2 / "02-next.md").write_text("# Next\n\n" + ("word " * 3000), encoding="utf-8")

    industry_dir = root / "Industries" / "Healthcare"
    industry_dir.mkdir(parents=True)
    (industry_dir / "healthcare-crash-course.md").write_text(
        "# Healthcare\n\nSector case.\n", encoding="utf-8"
    )

    (root / "skill_tree.yaml").write_text(
        """version: 1
guide_aliases:
  "00-legacy-guide": "01-core-guide"
tracks:
  foundations:
    title: Foundations
    guides:
      - id: "01-core-guide"
        prerequisites: []
      - id: "02-foundation-guide"
        prerequisites: ["01-core-guide"]
  industry:
    title: Industry
    guides:
      - id: "industry-healthcare"
        prerequisites: ["02-foundation-guide"]
programs:
  - id: "starter"
    title: Starter
    guides:
      - "01-core-guide"
    applied_modules:
      - "industry-healthcare"
""",
        encoding="utf-8",
    )

    report = audit_curriculum_root(root)

    assert report.guides_scanned == 3
    assert report.superseded_aliases == ["00-legacy-guide"]
    assert report.thin_guides[0].guide_id == "01-core-guide"
    assert report.thin_guides[0].rewrite_priority_score > 0
    assert report.applied_modules[0].guide_id == "industry-healthcare"
    assert report.applied_modules[0].recommended_role == "capstone"
