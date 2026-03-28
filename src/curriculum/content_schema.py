"""Curriculum content schema, parsing, linting, and migration helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

SCHEMA_VERSION = 1
SUPPORTED_CONTENT_SUFFIXES = (".md", ".mdx")

_ORDER_RE = re.compile(r"^(\d+)-")
_H1_RE = re.compile(r"^# (.+)$", re.MULTILINE)
_HEADING_RE = re.compile(r"^##+\s+(.+)$", re.MULTILINE)
_BULLET_RE = re.compile(r"^\s*[-*+]\s+(.*\S)\s*$")
_MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_CHAPTER_REF_RE = re.compile(r"curriculum:([A-Za-z0-9._/-]+)")
_SECTION_TITLE_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")
_TITLE_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")

_OBJECTIVE_SECTION_TOKENS = ("objective", "outcome", "learn", "key question")
_CHECKPOINT_SECTION_TOKENS = ("checkpoint", "review", "practice", "quiz", "self-check")
THIN_CHAPTER_WORD_THRESHOLD = 500


class CurriculumDocument(BaseModel):
    path: str
    title: str
    summary: str = ""
    objectives: list[str] = Field(default_factory=list)
    checkpoints: list[str] = Field(default_factory=list)
    content_references: list[str] = Field(default_factory=list)
    body: str = ""
    content_format: str = "markdown"
    schema_version: int = 0
    has_frontmatter: bool = False
    frontmatter_keys: list[str] = Field(default_factory=list)
    raw_metadata: dict[str, object] = Field(default_factory=dict)


class CurriculumLintIssue(BaseModel):
    code: str
    path: str
    message: str
    severity: str = "error"


class CurriculumLintReport(BaseModel):
    documents_scanned: int
    issues: list[CurriculumLintIssue] = Field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")


class CurriculumMigrationResult(BaseModel):
    documents_migrated: int = 0
    documents_skipped: int = 0
    output_root: str = ""
    outputs: list[str] = Field(default_factory=list)


class CurriculumAuditGuide(BaseModel):
    guide_id: str
    title: str
    chapter_count: int
    total_word_count: int
    track: str = ""
    program_ids: list[str] = Field(default_factory=list)
    dependent_count: int = 0
    recommended_role: str = "core"
    rewrite_priority_score: int = 0
    rationale: str = ""


class CurriculumAuditReport(BaseModel):
    guides_scanned: int
    thin_guides: list[CurriculumAuditGuide] = Field(default_factory=list)
    applied_modules: list[CurriculumAuditGuide] = Field(default_factory=list)
    superseded_aliases: list[str] = Field(default_factory=list)


def is_curriculum_content_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_CONTENT_SUFFIXES


def list_curriculum_content_files(directory: Path) -> list[Path]:
    files = [path for path in directory.iterdir() if is_curriculum_content_file(path)]
    deduped: dict[str, Path] = {}
    for path in sorted(files, key=lambda item: (item.stem, item.suffix != ".mdx", item.name)):
        existing = deduped.get(path.stem)
        if existing is None or path.suffix.lower() == ".mdx":
            deduped[path.stem] = path
    return sorted(deduped.values(), key=lambda item: item.name)


def iter_curriculum_content_files(root: Path) -> list[Path]:
    files = [path for path in root.rglob("*") if is_curriculum_content_file(path)]
    deduped: dict[tuple[str, str], Path] = {}
    for path in sorted(files, key=lambda item: (str(item.parent), item.stem, item.suffix != ".mdx")):
        key = (str(path.parent), path.stem)
        existing = deduped.get(key)
        if existing is None or path.suffix.lower() == ".mdx":
            deduped[key] = path
    return sorted(deduped.values())


def load_curriculum_document(path: Path) -> CurriculumDocument:
    raw_text = path.read_text(encoding="utf-8")
    metadata, body = _split_frontmatter(raw_text)
    has_frontmatter = bool(metadata)
    title = _normalize_scalar(metadata.get("title")) or extract_title_from_body(body, path.name)
    summary = _normalize_scalar(metadata.get("summary")) or infer_summary(body)
    objectives = _normalize_string_list(metadata.get("objectives")) or infer_objectives(body)
    checkpoints = _normalize_string_list(metadata.get("checkpoints")) or infer_checkpoints(body)
    references = _dedupe(
        _normalize_string_list(
            metadata.get("references")
            or metadata.get("content_references")
            or metadata.get("related_content")
        )
        + extract_content_references(body)
    )
    content_format = _normalize_scalar(metadata.get("content_format")) or _infer_content_format(path)
    schema_version = _coerce_int(metadata.get("schema_version"), default=1 if has_frontmatter else 0)

    return CurriculumDocument(
        path=str(path),
        title=title,
        summary=summary,
        objectives=objectives,
        checkpoints=checkpoints,
        content_references=references,
        body=body,
        content_format=content_format,
        schema_version=schema_version,
        has_frontmatter=has_frontmatter,
        frontmatter_keys=sorted(str(key) for key in metadata.keys()),
        raw_metadata=metadata,
    )


def extract_title_from_body(content: str, filename: str) -> str:
    match = _H1_RE.search(content)
    if match:
        return match.group(1).strip()
    stem = Path(filename).stem
    order_match = _ORDER_RE.match(stem)
    if order_match:
        stem = stem[order_match.end() :]
    return stem.replace("-", " ").replace("_", " ").title()


def infer_summary(content: str) -> str:
    for block in re.split(r"\n\s*\n", content):
        paragraph = block.strip()
        if not paragraph:
            continue
        if paragraph.startswith("#"):
            continue
        if _BULLET_RE.match(paragraph.splitlines()[0]):
            continue
        return " ".join(line.strip() for line in paragraph.splitlines())
    return ""


def infer_objectives(content: str) -> list[str]:
    section_items = _extract_section_list(content, _OBJECTIVE_SECTION_TOKENS)
    if section_items:
        return section_items[:5]

    headings = _extract_headings(content)
    candidates = [
        heading
        for heading in headings
        if _normalize_section_title(heading)
        not in {"overview", "summary", "introduction", "glossary", "conclusion"}
    ]
    if candidates:
        return [f"Understand {heading}" for heading in candidates[:3]]
    return []


def infer_checkpoints(content: str) -> list[str]:
    section_items = _extract_section_list(content, _CHECKPOINT_SECTION_TOKENS)
    if section_items:
        return section_items[:5]

    headings = _extract_headings(content)
    if headings:
        selected = headings[-3:]
        return [f"Explain the main idea behind {heading}" for heading in selected]
    return []


def extract_content_references(content: str) -> list[str]:
    refs = []
    refs.extend(match.group(1).strip() for match in _MARKDOWN_LINK_RE.finditer(content))
    refs.extend(match.group(1).strip() for match in _CHAPTER_REF_RE.finditer(content))
    return _dedupe(refs)


def resolve_chapter_content_path(
    content_dirs: list[Path], chapter_id: str, filename: str | None = None
) -> Path | None:
    parts = chapter_id.split("/", 1)
    if len(parts) != 2:
        return None

    guide_id, chapter_stem = parts
    candidate_names = []
    if filename:
        candidate_names.append(filename)
    candidate_names.extend([f"{chapter_stem}.mdx", f"{chapter_stem}.md"])

    for content_dir in content_dirs:
        guide_root = content_dir / guide_id
        for candidate_name in candidate_names:
            candidate = guide_root / candidate_name
            if candidate.is_file():
                return candidate

        if not guide_id.startswith("industry-"):
            continue

        industries_dir = content_dir / "Industries"
        if not industries_dir.is_dir():
            continue
        industry_name = guide_id[len("industry-") :]
        for subdir in industries_dir.iterdir():
            if not subdir.is_dir() or subdir.name.lower() != industry_name.lower():
                continue
            for candidate_name in candidate_names:
                candidate = subdir / candidate_name
                if candidate.is_file():
                    return candidate
    return None


def build_content_signature(document: CurriculumDocument) -> str:
    payload = {
        "schema_version": document.schema_version,
        "content_format": document.content_format,
        "title": document.title,
        "summary": document.summary,
        "objectives": document.objectives,
        "checkpoints": document.checkpoints,
        "content_references": document.content_references,
        "body": document.body,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def lint_curriculum_paths(paths: list[Path], root: Path | None = None) -> CurriculumLintReport:
    documents = [load_curriculum_document(path) for path in paths]
    path_lookup = {Path(document.path).resolve(): document for document in documents}
    id_lookup = {_chapter_id_for_path(Path(document.path)): document for document in documents}
    issues: list[CurriculumLintIssue] = []
    guides: dict[str, list[CurriculumDocument]] = {}

    for document in documents:
        path = Path(document.path)
        guide_id = _guide_id_for_path(path)
        guides.setdefault(guide_id, []).append(document)
        metadata = document.raw_metadata
        title = _normalize_scalar(metadata.get("title"))
        summary = _normalize_scalar(metadata.get("summary"))
        objectives = _normalize_string_list(metadata.get("objectives"))
        checkpoints = _normalize_string_list(metadata.get("checkpoints"))

        if not title:
            issues.append(
                CurriculumLintIssue(
                    code="missing_metadata",
                    path=str(path),
                    message="Missing required frontmatter field: title",
                )
            )
        if not summary:
            issues.append(
                CurriculumLintIssue(
                    code="missing_metadata",
                    path=str(path),
                    message="Missing required frontmatter field: summary",
                )
            )
        if not objectives:
            issues.append(
                CurriculumLintIssue(
                    code="missing_objectives",
                    path=str(path),
                    message="No declared learning objectives found in frontmatter",
                )
            )
        if not checkpoints:
            issues.append(
                CurriculumLintIssue(
                    code="missing_checkpoints",
                    path=str(path),
                    message="No declared checkpoints found in frontmatter",
                )
            )
        if not _is_glossary_path(path):
            word_count = len(document.body.split())
            if word_count < THIN_CHAPTER_WORD_THRESHOLD:
                issues.append(
                    CurriculumLintIssue(
                        code="thin_chapter",
                        path=str(path),
                        message=(
                            f"Thin chapter: {word_count} words "
                            f"(expected at least {THIN_CHAPTER_WORD_THRESHOLD})"
                        ),
                        severity="warning",
                    )
                )

        for reference in document.content_references:
            if _is_external_reference(reference):
                continue
            if not _reference_exists(reference, path, path_lookup, id_lookup):
                issues.append(
                    CurriculumLintIssue(
                        code="broken_content_reference",
                        path=str(path),
                        message=f"Broken content reference: {reference}",
                    )
                )

    for guide_id, guide_documents in guides.items():
        issues.extend(_lint_guide_sequence(guide_id, guide_documents))
        issues.extend(_lint_duplicate_titles(guide_id, guide_documents))

    if root is not None:
        issues.extend(_lint_curriculum_manifest(root, guides))

    issues.sort(key=lambda issue: (issue.path, issue.code, issue.message))
    return CurriculumLintReport(documents_scanned=len(documents), issues=issues)


def migrate_curriculum_corpus(
    source_root: Path, output_root: Path, overwrite: bool = False
) -> CurriculumMigrationResult:
    files = iter_curriculum_content_files(source_root)
    output_root.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []
    migrated = 0
    skipped = 0

    for path in files:
        document = load_curriculum_document(path)
        relative_path = path.relative_to(source_root)
        destination = output_root / relative_path.with_suffix(".mdx")
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists() and not overwrite:
            skipped += 1
            continue

        destination.write_text(render_mdx_document(document), encoding="utf-8")
        outputs.append(str(destination))
        migrated += 1

    manifest = source_root / "skill_tree.yaml"
    if manifest.is_file():
        destination_manifest = output_root / "skill_tree.yaml"
        if overwrite or not destination_manifest.exists():
            destination_manifest.write_text(manifest.read_text(encoding="utf-8"), encoding="utf-8")

    return CurriculumMigrationResult(
        documents_migrated=migrated,
        documents_skipped=skipped,
        output_root=str(output_root),
        outputs=outputs,
    )


def audit_curriculum_root(source_root: Path) -> CurriculumAuditReport:
    manifest = _load_curriculum_manifest(source_root)
    aliases = manifest.get("guide_aliases", {}) if isinstance(manifest.get("guide_aliases"), dict) else {}
    tracks = manifest.get("tracks", {}) if isinstance(manifest.get("tracks"), dict) else {}
    programs = manifest.get("programs", []) if isinstance(manifest.get("programs"), list) else []

    track_by_guide: dict[str, str] = {}
    dependents_by_guide: dict[str, set[str]] = {}
    for track_id, track_data in tracks.items():
        if not isinstance(track_data, dict):
            continue
        for entry in track_data.get("guides", []):
            if not isinstance(entry, dict):
                continue
            guide_id = str(entry.get("id", "")).strip()
            if not guide_id:
                continue
            track_by_guide[guide_id] = track_id
            dependents_by_guide.setdefault(guide_id, set())
            for prereq in entry.get("prerequisites", []):
                prereq_id = str(prereq).strip()
                if not prereq_id:
                    continue
                dependents_by_guide.setdefault(prereq_id, set()).add(guide_id)

    programs_by_guide: dict[str, set[str]] = {}
    for program in programs:
        if not isinstance(program, dict):
            continue
        program_id = str(program.get("id", "")).strip()
        if not program_id:
            continue
        for guide_id in program.get("guides", []):
            guide_text = str(guide_id).strip()
            if guide_text:
                programs_by_guide.setdefault(guide_text, set()).add(program_id)
        for guide_id in program.get("applied_modules", []):
            guide_text = str(guide_id).strip()
            if guide_text:
                programs_by_guide.setdefault(guide_text, set()).add(program_id)

    guides: list[CurriculumAuditGuide] = []
    industries_dir = source_root / "Industries"
    directories = [entry for entry in sorted(source_root.iterdir()) if entry.is_dir()]
    for directory in directories:
        if directory.name.startswith("."):
            continue
        if directory.name == "Industries":
            for industry_dir in sorted(industries_dir.iterdir()):
                if not industry_dir.is_dir() or industry_dir.name.startswith("."):
                    continue
                files = list_curriculum_content_files(industry_dir)
                if not files:
                    continue
                guide_id = f"industry-{industry_dir.name.lower()}"
                guides.append(
                    _build_audit_guide(
                        guide_id=guide_id,
                        title=f"{industry_dir.name} Industry",
                        files=files,
                        track=track_by_guide.get(guide_id, "industry"),
                        program_ids=sorted(programs_by_guide.get(guide_id, set())),
                        dependent_count=len(dependents_by_guide.get(guide_id, set())),
                        recommended_role="capstone",
                    )
                )
            continue

        files = list_curriculum_content_files(directory)
        if not files:
            continue
        guide_id = directory.name
        recommended_role = "superseded" if guide_id in aliases else "core"
        guides.append(
            _build_audit_guide(
                guide_id=guide_id,
                title=_title_from_guide_id(guide_id),
                files=files,
                track=track_by_guide.get(guide_id, ""),
                program_ids=sorted(programs_by_guide.get(guide_id, set())),
                dependent_count=len(dependents_by_guide.get(guide_id, set())),
                recommended_role=recommended_role,
            )
        )

    thin_guides = [
        guide
        for guide in guides
        if guide.recommended_role == "core"
        and (guide.chapter_count <= 1 or guide.total_word_count < 16000)
    ]
    for guide in thin_guides:
        score = 0
        if guide.chapter_count <= 1:
            score += 60
        score += max(0, (16000 - guide.total_word_count) // 500)
        score += guide.dependent_count * 8
        score += len(guide.program_ids) * 4
        guide.rewrite_priority_score = int(score)
        guide.rationale = _rewrite_rationale(guide)

    thin_guides.sort(
        key=lambda guide: (
            -guide.rewrite_priority_score,
            guide.chapter_count,
            guide.total_word_count,
            guide.guide_id,
        )
    )

    applied_modules = [guide for guide in guides if guide.recommended_role == "capstone"]
    for guide in applied_modules:
        guide.rationale = (
            "One-file industry module; treat as an applied capstone before any deep rewrite."
        )

    applied_modules.sort(key=lambda guide: guide.guide_id)

    return CurriculumAuditReport(
        guides_scanned=len(guides),
        thin_guides=thin_guides,
        applied_modules=applied_modules,
        superseded_aliases=sorted(str(alias) for alias in aliases.keys()),
    )


def render_mdx_document(document: CurriculumDocument) -> str:
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "title": document.title,
        "summary": document.summary,
        "objectives": document.objectives,
        "checkpoints": document.checkpoints,
        "references": document.content_references,
        "content_format": "mdx",
    }
    frontmatter_text = yaml.safe_dump(
        metadata, sort_keys=False, allow_unicode=True, default_flow_style=False
    ).strip()
    body = document.body.rstrip()
    return f"---\n{frontmatter_text}\n---\n\n{body}\n"


def _split_frontmatter(raw_text: str) -> tuple[dict[str, object], str]:
    if not raw_text.startswith("---\n") and not raw_text.startswith("---\r\n"):
        return {}, raw_text.strip()

    lines = raw_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, raw_text.strip()

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}, raw_text.strip()

    frontmatter_text = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :]).strip()
    try:
        metadata = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        metadata = {}
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, body


def _extract_headings(content: str) -> list[str]:
    return [match.group(1).strip() for match in _HEADING_RE.finditer(content)]


def _extract_section_list(content: str, tokens: tuple[str, ...]) -> list[str]:
    lines = content.splitlines()
    for index, raw_line in enumerate(lines):
        if not raw_line.startswith("##"):
            continue
        heading = raw_line.lstrip("#").strip().lower()
        if not any(token in heading for token in tokens):
            continue
        items: list[str] = []
        for next_line in lines[index + 1 :]:
            if next_line.startswith("##"):
                break
            match = _BULLET_RE.match(next_line)
            if match:
                items.append(match.group(1).strip())
        if items:
            return items
    return []


def _normalize_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        normalized = value.strip()
        return [normalized] if normalized else []
    if isinstance(value, (list, tuple)):
        results = []
        for item in value:
            normalized = _normalize_scalar(item)
            if normalized:
                results.append(normalized)
        return results
    return []


def _normalize_scalar(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _infer_content_format(path: Path) -> str:
    return "mdx" if path.suffix.lower() == ".mdx" else "markdown"


def _coerce_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _chapter_id_for_path(path: Path) -> str:
    parts = path.parts
    if "Industries" in parts:
        index = parts.index("Industries")
        industry_name = parts[index + 1].lower()
        return f"industry-{industry_name}/{path.stem}"
    parent_name = path.parent.name
    return f"{parent_name}/{path.stem}"


def _guide_id_for_path(path: Path) -> str:
    return _chapter_id_for_path(path).split("/", 1)[0]


def _chapter_order(path: Path) -> int | None:
    match = _ORDER_RE.match(path.stem)
    if not match:
        return None
    return int(match.group(1))


def _is_glossary_path(path: Path) -> bool:
    return "glossary" in path.stem.lower()


def _is_external_reference(reference: str) -> bool:
    lower = reference.lower()
    return lower.startswith(("http://", "https://", "mailto:", "#"))


def _reference_exists(
    reference: str,
    source_path: Path,
    path_lookup: dict[Path, CurriculumDocument],
    id_lookup: dict[str, CurriculumDocument],
) -> bool:
    if reference.startswith("curriculum:"):
        return reference[len("curriculum:") :] in id_lookup
    if reference.startswith("/learn/"):
        parts = [part for part in reference.split("/") if part]
        if len(parts) >= 3:
            return f"{parts[1]}/{parts[2]}" in id_lookup
        return False
    if reference in id_lookup:
        return True

    candidate = (source_path.parent / reference).resolve()
    if candidate in path_lookup:
        return True
    if candidate.suffix.lower() not in SUPPORTED_CONTENT_SUFFIXES:
        for suffix in SUPPORTED_CONTENT_SUFFIXES:
            alternate = candidate.with_suffix(suffix)
            if alternate in path_lookup:
                return True
    return False


def _lint_guide_sequence(
    guide_id: str, guide_documents: list[CurriculumDocument]
) -> list[CurriculumLintIssue]:
    numbered_paths: dict[int, list[Path]] = {}
    for document in guide_documents:
        path = Path(document.path)
        order = _chapter_order(path)
        if order is None:
            continue
        numbered_paths.setdefault(order, []).append(path)

    issues: list[CurriculumLintIssue] = []
    for order, paths in sorted(numbered_paths.items()):
        if len(paths) <= 1:
            continue
        joined = ", ".join(path.name for path in sorted(paths))
        issues.append(
            CurriculumLintIssue(
                code="duplicate_chapter_order",
                path=str(sorted(paths)[0]),
                message=f"Guide {guide_id} reuses chapter order {order:02d}: {joined}",
            )
        )

    if not numbered_paths:
        return issues

    highest_order = max(numbered_paths)
    missing_orders = [order for order in range(1, highest_order + 1) if order not in numbered_paths]
    if missing_orders:
        formatted = ", ".join(f"{order:02d}" for order in missing_orders)
        issues.append(
            CurriculumLintIssue(
                code="path_gap",
                path=str(sorted(Path(document.path) for document in guide_documents)[0]),
                message=f"Guide {guide_id} has chapter order gaps: {formatted}",
            )
        )
    return issues


def _lint_duplicate_titles(
    guide_id: str, guide_documents: list[CurriculumDocument]
) -> list[CurriculumLintIssue]:
    titles: dict[str, list[CurriculumDocument]] = {}
    for document in guide_documents:
        normalized = _normalize_title(document.title)
        if normalized:
            titles.setdefault(normalized, []).append(document)

    issues: list[CurriculumLintIssue] = []
    for documents in titles.values():
        if len(documents) <= 1:
            continue
        ordered_documents = sorted(documents, key=lambda item: item.path)
        joined = ", ".join(Path(document.path).name for document in ordered_documents)
        issues.append(
            CurriculumLintIssue(
                code="duplicate_concept",
                path=ordered_documents[0].path,
                message=(
                    f"Guide {_normalize_scalar(guide_id)} repeats chapter title "
                    f"'{ordered_documents[0].title}': {joined}"
                ),
                severity="warning",
            )
        )
    return issues


def _lint_curriculum_manifest(
    source_root: Path, guide_documents: dict[str, list[CurriculumDocument]]
) -> list[CurriculumLintIssue]:
    data = _load_curriculum_manifest(source_root)
    if not data:
        return []

    manifest_path = source_root / "skill_tree.yaml"
    available_guides = set(guide_documents.keys())
    raw_aliases = data.get("guide_aliases", {})
    aliases = raw_aliases if isinstance(raw_aliases, dict) else {}
    tracks = data.get("tracks", {})
    programs = data.get("programs", [])
    issues: list[CurriculumLintIssue] = []

    for alias, target in aliases.items():
        if not isinstance(alias, str) or not isinstance(target, str):
            continue
        canonical = _canonicalize_manifest_guide_id(target, aliases)
        if canonical not in available_guides:
            issues.append(
                CurriculumLintIssue(
                    code="unknown_guide_alias_target",
                    path=str(manifest_path),
                    message=f"Guide alias '{alias}' points to missing guide '{target}'",
                )
            )

    graph: dict[str, list[str]] = {}
    track_assignments: dict[str, str] = {}
    if isinstance(tracks, dict):
        for track_id, track_data in tracks.items():
            if not isinstance(track_data, dict):
                continue
            for entry in track_data.get("guides", []):
                if not isinstance(entry, dict):
                    continue
                raw_guide_id = _normalize_scalar(entry.get("id"))
                if not raw_guide_id:
                    continue
                guide_id = _canonicalize_manifest_guide_id(raw_guide_id, aliases)
                graph.setdefault(guide_id, [])
                if guide_id not in available_guides:
                    issues.append(
                        CurriculumLintIssue(
                            code="unknown_manifest_guide",
                            path=str(manifest_path),
                            message=f"Track '{track_id}' references missing guide '{raw_guide_id}'",
                        )
                    )
                    continue
                previous_track = track_assignments.get(guide_id)
                if previous_track is not None and previous_track != track_id:
                    issues.append(
                        CurriculumLintIssue(
                            code="duplicate_track_assignment",
                            path=str(manifest_path),
                            message=(
                                f"Guide '{guide_id}' appears in both '{previous_track}' and '{track_id}'"
                            ),
                        )
                    )
                track_assignments[guide_id] = track_id

                prereqs = []
                for raw_prereq in entry.get("prerequisites", []):
                    prereq_id = _canonicalize_manifest_guide_id(
                        _normalize_scalar(raw_prereq), aliases
                    )
                    if not prereq_id:
                        continue
                    prereqs.append(prereq_id)
                    if prereq_id not in available_guides:
                        issues.append(
                            CurriculumLintIssue(
                                code="unknown_prerequisite",
                                path=str(manifest_path),
                                message=(
                                    f"Guide '{guide_id}' references missing prerequisite "
                                    f"'{raw_prereq}'"
                                ),
                            )
                        )
                graph[guide_id] = list(dict.fromkeys(prereqs))

    untracked_guides = sorted(available_guides - set(track_assignments) - set(aliases))
    for guide_id in untracked_guides:
        issues.append(
            CurriculumLintIssue(
                code="missing_track_assignment",
                path=str(manifest_path),
                message=f"Guide '{guide_id}' is present in content but missing from tracks",
            )
        )

    if isinstance(programs, list):
        for program in programs:
            if not isinstance(program, dict):
                continue
            program_id = _normalize_scalar(program.get("id")) or "<unknown>"
            for field in ("guides", "applied_modules"):
                for raw_guide_id in program.get(field, []):
                    guide_id = _canonicalize_manifest_guide_id(
                        _normalize_scalar(raw_guide_id), aliases
                    )
                    if guide_id and guide_id not in available_guides:
                        issues.append(
                            CurriculumLintIssue(
                                code="unknown_program_reference",
                                path=str(manifest_path),
                                message=(
                                    f"Program '{program_id}' references missing guide "
                                    f"'{raw_guide_id}' in '{field}'"
                                ),
                            )
                        )

    issues.extend(_lint_prerequisite_cycles(graph, manifest_path))
    return issues


def _lint_prerequisite_cycles(graph: dict[str, list[str]], manifest_path: Path) -> list[CurriculumLintIssue]:
    states: dict[str, int] = {}
    stack: list[str] = []
    cycle_paths: dict[tuple[str, ...], list[str]] = {}

    def visit(node: str):
        state = states.get(node, 0)
        if state == 1:
            if node in stack:
                cycle = stack[stack.index(node) :] + [node]
                cycle_paths.setdefault(tuple(sorted(set(cycle[:-1]))), cycle)
            return
        if state == 2:
            return

        states[node] = 1
        stack.append(node)
        for prereq in graph.get(node, []):
            if prereq in graph:
                visit(prereq)
        stack.pop()
        states[node] = 2

    for node in sorted(graph):
        visit(node)

    return [
        CurriculumLintIssue(
            code="prerequisite_cycle",
            path=str(manifest_path),
            message=f"Prerequisite cycle detected: {' -> '.join(cycle)}",
        )
        for cycle in cycle_paths.values()
    ]


def _canonicalize_manifest_guide_id(guide_id: str, aliases: dict[str, str]) -> str:
    current = guide_id
    seen = {current}
    while current in aliases and aliases[current] not in seen:
        current = aliases[current]
        seen.add(current)
    return current


def _normalize_section_title(title: str) -> str:
    return _SECTION_TITLE_NORMALIZE_RE.sub("", title.lower())


def _normalize_title(title: str) -> str:
    return _TITLE_NORMALIZE_RE.sub(" ", title.lower()).strip()


def _load_curriculum_manifest(source_root: Path) -> dict[str, object]:
    manifest = source_root / "skill_tree.yaml"
    if not manifest.is_file():
        return {}
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _build_audit_guide(
    *,
    guide_id: str,
    title: str,
    files: list[Path],
    track: str,
    program_ids: list[str],
    dependent_count: int,
    recommended_role: str,
) -> CurriculumAuditGuide:
    total_words = 0
    for file in files:
        document = load_curriculum_document(file)
        total_words += len(document.body.split())
    return CurriculumAuditGuide(
        guide_id=guide_id,
        title=title,
        chapter_count=len(files),
        total_word_count=total_words,
        track=track,
        program_ids=program_ids,
        dependent_count=dependent_count,
        recommended_role=recommended_role,
    )


def _title_from_guide_id(guide_id: str) -> str:
    stem = guide_id
    order_match = _ORDER_RE.match(stem)
    if order_match:
        stem = stem[order_match.end() :]
    for suffix in ("-guide", "-curriculum", "-crash-course"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem.replace("-", " ").replace("_", " ").title()


def _rewrite_rationale(guide: CurriculumAuditGuide) -> str:
    reasons = []
    if guide.chapter_count <= 1:
        reasons.append("single-file guide")
    else:
        reasons.append(f"{guide.total_word_count:,} words across {guide.chapter_count} chapters")
    if guide.dependent_count:
        reasons.append(f"unlocks {guide.dependent_count} downstream guide(s)")
    if guide.program_ids:
        reasons.append(f"appears in {len(guide.program_ids)} program(s)")
    return ", ".join(reasons)
