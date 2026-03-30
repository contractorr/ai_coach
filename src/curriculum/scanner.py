"""Scan content directories to discover guides and chapters."""

import hashlib
import re
from pathlib import Path
from typing import Any

import structlog
import yaml

from .content_schema import (
    build_content_signature,
    extract_title_from_body,
    list_curriculum_content_files,
    load_curriculum_document,
    load_manifest_guide_titles,
)
from .models import Chapter, DifficultyLevel, Guide, GuideCategory, GuideKind, GuideOrigin
from .user_content import load_guide_metadata

logger = structlog.get_logger()

# Regex for extracting order prefix from filenames like "01-introduction.md"
_ORDER_RE = re.compile(r"^(\d+)-")

# Box-drawing characters (U+2500–U+257F) and common ASCII art patterns
_BOX_DRAWING_RE = re.compile(r"[\u2500-\u257F]")
_ASCII_ART_RE = re.compile(r"[+|]\-{3,}[+|]|[+|]{2,}\-|─{3,}|═{3,}|╔|╗|╚|╝|├|┤|┌|┐|└|┘")
_TABLE_SEP_RE = re.compile(r"^\s*[-|:]+\s*$")
_FORMULA_RE = re.compile(r"\$[^$]+\$|\\frac|\\sum|\\int|\\sqrt|∑|∫|√|≈|≠|≤|≥|∈|∀|∃")

# Words per minute for reading time estimates
_WPM = 250

# Category inference from directory name keywords
_CATEGORY_KEYWORDS: dict[str, GuideCategory] = {
    "philosophy": GuideCategory.HUMANITIES,
    "epistemology": GuideCategory.HUMANITIES,
    "religion": GuideCategory.HUMANITIES,
    "theology": GuideCategory.HUMANITIES,
    "history": GuideCategory.HUMANITIES,
    "geography": GuideCategory.SOCIAL_SCIENCE,
    "linguistics": GuideCategory.HUMANITIES,
    "world-history": GuideCategory.HUMANITIES,
    "mathematics": GuideCategory.SCIENCE,
    "statistics": GuideCategory.SCIENCE,
    "physics": GuideCategory.SCIENCE,
    "chemistry": GuideCategory.SCIENCE,
    "classics": GuideCategory.HUMANITIES,
    "biology": GuideCategory.SCIENCE,
    "genetics": GuideCategory.SCIENCE,
    "ecology": GuideCategory.SCIENCE,
    "geology": GuideCategory.SCIENCE,
    "oceanography": GuideCategory.SCIENCE,
    "climate": GuideCategory.SCIENCE,
    "energy": GuideCategory.SCIENCE,
    "medicine": GuideCategory.SCIENCE,
    "neuroscience": GuideCategory.SCIENCE,
    "cognitive": GuideCategory.SCIENCE,
    "economics": GuideCategory.BUSINESS,
    "accounting": GuideCategory.BUSINESS,
    "finance": GuideCategory.BUSINESS,
    "mba": GuideCategory.BUSINESS,
    "private-markets": GuideCategory.BUSINESS,
    "game-theory": GuideCategory.SOCIAL_SCIENCE,
    "psychology": GuideCategory.SOCIAL_SCIENCE,
    "sociology": GuideCategory.SOCIAL_SCIENCE,
    "demography": GuideCategory.SOCIAL_SCIENCE,
    "government": GuideCategory.SOCIAL_SCIENCE,
    "politics": GuideCategory.SOCIAL_SCIENCE,
    "law": GuideCategory.SOCIAL_SCIENCE,
    "geopolitics": GuideCategory.SOCIAL_SCIENCE,
    "computer-science": GuideCategory.TECHNOLOGY,
    "ai-ml": GuideCategory.TECHNOLOGY,
    "cybersecurity": GuideCategory.TECHNOLOGY,
    "engineering": GuideCategory.TECHNOLOGY,
    "information-theory": GuideCategory.TECHNOLOGY,
    "agriculture": GuideCategory.SCIENCE,
    "complex-systems": GuideCategory.SCIENCE,
}

_INDUSTRY_CATEGORY = GuideCategory.INDUSTRY

# Difficulty heuristics based on guide order (lower = more introductory)
_ADVANCED_KEYWORDS = {"private-markets", "geopolitics", "cybersecurity", "ai-ml"}
_INTRO_KEYWORDS = {"introduction", "fundamentals", "crash-course"}
_CATALOG_CONTENT_SUFFIXES = {".md", ".mdx"}
_CATALOG_METADATA_FILENAMES = {"skill_tree.yaml", "guide.yaml"}


def _infer_category(dir_name: str, is_industry: bool = False) -> GuideCategory:
    if is_industry:
        return _INDUSTRY_CATEGORY
    lower = dir_name.lower()
    for keyword, cat in _CATEGORY_KEYWORDS.items():
        if keyword in lower:
            return cat
    return GuideCategory.PROFESSIONAL


def _infer_difficulty(dir_name: str, order: int) -> DifficultyLevel:
    lower = dir_name.lower()
    if any(kw in lower for kw in _ADVANCED_KEYWORDS):
        return DifficultyLevel.ADVANCED
    if any(kw in lower for kw in _INTRO_KEYWORDS) or order <= 5:
        return DifficultyLevel.INTRODUCTORY
    if order <= 20:
        return DifficultyLevel.INTERMEDIATE
    return DifficultyLevel.ADVANCED


def _extract_title(content: str, filename: str) -> str:
    """Extract title from first H1 heading or derive from filename."""
    return extract_title_from_body(content, filename)


def _detect_diagrams(content: str) -> bool:
    return bool(_BOX_DRAWING_RE.search(content) or _ASCII_ART_RE.search(content))


def _detect_tables(content: str) -> bool:
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "|" in line and i + 1 < len(lines) and _TABLE_SEP_RE.match(lines[i + 1]):
            return True
    return False


def _detect_formulas(content: str) -> bool:
    return bool(_FORMULA_RE.search(content))


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _compute_catalog_fingerprint(content_dirs: list[Path]) -> str:
    """Hash curriculum content + metadata file paths and stat info."""
    digest = hashlib.sha256()
    for content_dir in sorted((Path(d).expanduser().resolve() for d in content_dirs), key=str):
        digest.update(str(content_dir).encode("utf-8"))
        if not content_dir.exists():
            digest.update(b":missing")
            continue
        for path in sorted(
            content_dir.rglob("*"), key=lambda item: str(item.relative_to(content_dir))
        ):
            if not path.is_file():
                continue
            if (
                path.suffix.lower() not in _CATALOG_CONTENT_SUFFIXES
                and path.name not in _CATALOG_METADATA_FILENAMES
            ):
                continue
            stat = path.stat()
            relative_path = path.relative_to(content_dir)
            digest.update(str(relative_path).encode("utf-8"))
            digest.update(str(stat.st_size).encode("utf-8"))
            digest.update(str(stat.st_mtime_ns).encode("utf-8"))
    return digest.hexdigest()


def _guide_title_from_dir(dir_name: str) -> str:
    """Derive guide title from directory name."""
    m = _ORDER_RE.match(dir_name)
    stem = dir_name[m.end() :] if m else dir_name
    # Remove trailing -guide, -curriculum, -crash-course
    for suffix in ["-guide", "-curriculum", "-crash-course"]:
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem.replace("-", " ").replace("_", " ").title()


def _guide_order(dir_name: str) -> int:
    m = _ORDER_RE.match(dir_name)
    return int(m.group(1)) if m else 99


def _coerce_category(value: object, fallback: GuideCategory) -> GuideCategory:
    if isinstance(value, str):
        try:
            return GuideCategory(value)
        except ValueError:
            return fallback
    return fallback


def _coerce_difficulty(value: object, fallback: DifficultyLevel) -> DifficultyLevel:
    if isinstance(value, str):
        try:
            return DifficultyLevel(value)
        except ValueError:
            return fallback
    return fallback


def _coerce_origin(value: object) -> GuideOrigin:
    if isinstance(value, str):
        try:
            return GuideOrigin(value)
        except ValueError:
            return GuideOrigin.BUILTIN
    return GuideOrigin.BUILTIN


def _coerce_kind(value: object, fallback: GuideKind = GuideKind.CORE) -> GuideKind:
    if isinstance(value, str):
        try:
            return GuideKind(value)
        except ValueError:
            return fallback
    return fallback


def _load_manifest_data(content_dir: Path) -> dict[str, Any] | None:
    """Load and validate skill_tree.yaml root data."""
    manifest = content_dir / "skill_tree.yaml"
    if not manifest.is_file():
        return None
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("skill_tree.invalid_yaml", path=str(manifest))
        return None
    if not isinstance(data, dict) or "tracks" not in data:
        return None
    return data


def _canonicalize_guide_id(guide_id: str, guide_aliases: dict[str, str]) -> str:
    """Resolve a guide ID through manifest alias mappings."""
    current = guide_id
    seen = {current}
    while current in guide_aliases and guide_aliases[current] not in seen:
        current = guide_aliases[current]
        seen.add(current)
    return current


def load_skill_tree(
    content_dir: Path,
) -> tuple[dict[str, list[str]], dict[str, str], dict[str, dict]] | None:
    """Load skill_tree.yaml from content_dir.

    Returns (guide_prereqs, guide_tracks, track_metadata) or None.
    """
    data = _load_manifest_data(content_dir)
    if data is None:
        return None
    guide_aliases = load_guide_aliases(content_dir)

    guide_prereqs: dict[str, list[str]] = {}
    guide_tracks: dict[str, str] = {}
    track_metadata: dict[str, dict] = {}

    for track_id, track_data in data["tracks"].items():
        track_metadata[track_id] = {
            "title": track_data.get("title", track_id),
            "description": track_data.get("description", ""),
            "color": track_data.get("color", "#6b7280"),
        }
        for entry in track_data.get("guides", []):
            gid = _canonicalize_guide_id(entry["id"], guide_aliases)
            prereqs = [
                _canonicalize_guide_id(prereq, guide_aliases)
                for prereq in entry.get("prerequisites", [])
            ]
            guide_prereqs[gid] = list(dict.fromkeys(prereqs))
            guide_tracks[gid] = track_id

    return guide_prereqs, guide_tracks, track_metadata


def load_guide_aliases(content_dir: Path) -> dict[str, str]:
    """Load alias -> canonical guide mappings from the manifest."""
    data = _load_manifest_data(content_dir)
    if data is None:
        return {}

    raw_aliases = data.get("guide_aliases", {})
    if not isinstance(raw_aliases, dict):
        return {}

    aliases: dict[str, str] = {}
    for alias, canonical in raw_aliases.items():
        if not isinstance(alias, str) or not isinstance(canonical, str):
            continue
        aliases[alias] = canonical

    resolved: dict[str, str] = {}
    for alias, canonical in aliases.items():
        final_canonical = _canonicalize_guide_id(canonical, aliases)
        if alias != final_canonical:
            resolved[alias] = final_canonical
    return resolved


def load_learning_programs(content_dir: Path) -> list[dict]:
    """Load curated learning programs from the manifest."""
    data = _load_manifest_data(content_dir)
    if data is None:
        return []

    guide_aliases = load_guide_aliases(content_dir)
    raw_programs = data.get("programs", [])
    if not isinstance(raw_programs, list):
        return []

    programs: list[dict] = []
    for entry in raw_programs:
        if not isinstance(entry, dict):
            continue
        program_id = entry.get("id")
        if not isinstance(program_id, str) or not program_id:
            continue

        guide_ids: list[str] = []
        seen_guide_ids: set[str] = set()
        for raw_guide_id in entry.get("guides", []):
            if not isinstance(raw_guide_id, str):
                continue
            guide_id = _canonicalize_guide_id(raw_guide_id, guide_aliases)
            if guide_id in seen_guide_ids:
                continue
            seen_guide_ids.add(guide_id)
            guide_ids.append(guide_id)

        applied_module_ids: list[str] = []
        seen_applied_module_ids: set[str] = set()
        for raw_guide_id in entry.get("applied_modules", []):
            if not isinstance(raw_guide_id, str):
                continue
            guide_id = _canonicalize_guide_id(raw_guide_id, guide_aliases)
            if guide_id in seen_applied_module_ids:
                continue
            seen_applied_module_ids.add(guide_id)
            applied_module_ids.append(guide_id)

        programs.append(
            {
                "id": program_id,
                "title": entry.get("title", program_id),
                "audience": entry.get("audience", ""),
                "description": entry.get("description", ""),
                "color": entry.get("color", "#6b7280"),
                "outcomes": [
                    outcome for outcome in entry.get("outcomes", []) if isinstance(outcome, str)
                ],
                "guide_ids": guide_ids,
                "applied_module_ids": applied_module_ids,
            }
        )

    return programs


def build_tree_layout(
    skill_tree: tuple[dict[str, list[str]], dict[str, str], dict[str, dict]] | None,
) -> dict[str, dict]:
    """Compute layout positions for skill tree DAG via topological sort.

    Returns dict[guide_id -> {x, y, depth}].
    Uses longest-path-from-root to assign depth, then indexes within each tier for x.
    """
    if skill_tree is None:
        return {}

    guide_prereqs, guide_tracks, _ = skill_tree

    if not guide_prereqs:
        return {}

    all_guides = set(guide_prereqs.keys())

    # Compute depth = longest path from any root (entry point)
    depth: dict[str, int] = {}

    # Build children adjacency: prereq -> list of dependents
    children: dict[str, list[str]] = {gid: [] for gid in all_guides}
    for gid, prereqs in guide_prereqs.items():
        for p in prereqs:
            if p in children:
                children[p].append(gid)

    # BFS computing longest path (process each node, relax edges)
    # Initialize entry points (no prereqs) at depth 0
    from collections import deque

    for gid, prereqs in guide_prereqs.items():
        valid_prereqs = [p for p in prereqs if p in all_guides]
        if not valid_prereqs:
            depth[gid] = 0

    # Relax: BFS from depth-0 nodes, always taking max depth
    queue = deque(gid for gid in depth)
    while queue:
        gid = queue.popleft()
        for child in children[gid]:
            new_depth = depth[gid] + 1
            if child not in depth or new_depth > depth[child]:
                depth[child] = new_depth
                queue.append(child)

    # Assign x = index within same depth tier
    tiers: dict[int, list[str]] = {}
    for gid, d in depth.items():
        tiers.setdefault(d, []).append(gid)

    positions: dict[str, dict] = {}
    for d, guides in tiers.items():
        guides.sort()  # deterministic ordering
        for x, gid in enumerate(guides):
            positions[gid] = {"x": x, "y": d, "depth": d}

    return positions


class CurriculumScanner:
    """Walks content directories and discovers guides + chapters."""

    def __init__(self, content_dirs: list[Path]):
        self.content_dirs = [Path(d).expanduser().resolve() for d in content_dirs]
        self._skill_tree: tuple[dict[str, list[str]], dict[str, str], dict[str, dict]] | None = None
        self._learning_programs: list[dict] = []
        self._guide_aliases: dict[str, str] = {}
        self._guide_titles: dict[str, str] = {}
        for d in self.content_dirs:
            result = load_skill_tree(d)
            programs = load_learning_programs(d)
            aliases = load_guide_aliases(d)
            guide_titles = load_manifest_guide_titles(d)
            if result is not None or programs or aliases or guide_titles:
                self._skill_tree = result
                self._learning_programs = programs
                self._guide_aliases = aliases
                self._guide_titles = guide_titles
                break

    def get_track_metadata(self) -> dict[str, dict]:
        """Return track id -> {title, description, color} from manifest."""
        if self._skill_tree is None:
            return {}
        return self._skill_tree[2]

    def get_manifest_guide_ids(self) -> set[str]:
        """Return canonical guide IDs explicitly tracked by the manifest."""
        if self._skill_tree is None:
            return set()
        return set(self._skill_tree[1].keys())

    def get_learning_programs(self) -> list[dict]:
        """Return curated learning programs from the manifest."""
        return list(self._learning_programs)

    def get_guide_aliases(self) -> dict[str, str]:
        """Return alias -> canonical guide mappings from the manifest."""
        return dict(self._guide_aliases)

    def get_catalog_fingerprint(self) -> str:
        """Return a fingerprint for curriculum content and manifest metadata."""
        return _compute_catalog_fingerprint(self.content_dirs)

    def canonicalize_guide_id(self, guide_id: str) -> str:
        """Resolve a guide ID through manifest aliases when present."""
        return _canonicalize_guide_id(guide_id, self._guide_aliases)

    def scan(self) -> tuple[list[Guide], list[Chapter]]:
        """Scan all content dirs and return (guides, chapters)."""
        guides: list[Guide] = []
        chapters: list[Chapter] = []
        seen_guide_ids: set[str] = set()

        for content_dir in self.content_dirs:
            if not content_dir.exists():
                logger.warning("curriculum.scan.dir_missing", path=str(content_dir))
                continue
            self._scan_dir(content_dir, guides, chapters, seen_guide_ids)

        guides.sort(key=lambda g: (_guide_order(g.id), g.title))
        return guides, chapters

    def _scan_dir(
        self,
        base: Path,
        guides: list[Guide],
        chapters: list[Chapter],
        seen: set[str],
    ) -> None:
        # Look for NN-*-guide/ directories and Industries/ subdirs
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue
            name = entry.name

            if name == "Industries":
                self._scan_industries(entry, guides, chapters, seen)
                continue

            # Skip hidden dirs and non-guide dirs
            if name.startswith("."):
                continue

            chapter_files = list_curriculum_content_files(entry)
            if not chapter_files:
                continue

            if name in seen:
                continue
            seen.add(name)

            guide, guide_chapters = self._build_guide(entry, name, chapter_files, is_industry=False)
            guides.append(guide)
            chapters.extend(guide_chapters)

    def _scan_industries(
        self,
        industries_dir: Path,
        guides: list[Guide],
        chapters: list[Chapter],
        seen: set[str],
    ) -> None:
        for entry in sorted(industries_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            chapter_files = list_curriculum_content_files(entry)
            if not chapter_files:
                continue

            guide_id = f"industry-{entry.name.lower()}"
            if guide_id in seen:
                continue
            seen.add(guide_id)

            guide, guide_chapters = self._build_guide(
                entry, guide_id, chapter_files, is_industry=True
            )
            guide.title = self._guide_titles.get(guide_id, f"{entry.name} Industry")
            guides.append(guide)
            chapters.extend(guide_chapters)

    def _build_guide(
        self,
        guide_dir: Path,
        guide_id: str,
        chapter_files: list[Path],
        is_industry: bool,
    ) -> tuple[Guide, list[Chapter]]:
        order = _guide_order(guide_id)
        guide_chapters: list[Chapter] = []
        total_words = 0
        has_glossary = False
        guide_metadata = load_guide_metadata(guide_dir)

        for idx, chapter_file in enumerate(chapter_files):
            try:
                document = load_curriculum_document(chapter_file)
            except Exception:
                logger.warning("curriculum.scan.read_error", file=str(chapter_file))
                continue

            words = len(document.body.split())
            total_words += words
            is_glossary = "glossary" in chapter_file.stem.lower()
            if is_glossary:
                has_glossary = True

            chapter_id = f"{guide_id}/{chapter_file.stem}"
            content_signature = build_content_signature(document)
            chapter = Chapter(
                id=chapter_id,
                guide_id=guide_id,
                title=document.title,
                filename=chapter_file.name,
                order=idx,
                summary=document.summary,
                objectives=document.objectives,
                checkpoints=document.checkpoints,
                content_references=document.content_references,
                content_format=document.content_format,
                schema_version=document.schema_version,
                word_count=words,
                reading_time_minutes=max(1, words // _WPM),
                has_diagrams=_detect_diagrams(document.body),
                has_tables=_detect_tables(document.body),
                has_formulas=_detect_formulas(document.body),
                is_glossary=is_glossary,
                content_hash=_content_hash(content_signature),
            )
            guide_chapters.append(chapter)

        reading_time = sum(c.reading_time_minutes for c in guide_chapters)

        # Prereqs + track from manifest, fallback to auto-inferred ordering
        if self._skill_tree and guide_id in self._skill_tree[0]:
            prereqs = self._skill_tree[0][guide_id]
            track = self._skill_tree[1].get(guide_id, "")
        else:
            prereqs = []
            track = ""
            if order > 1 and not is_industry:
                prev = f"{order - 1:02d}-"
                for d in (guide_dir.parent).iterdir():
                    if d.is_dir() and d.name.startswith(prev):
                        prereqs.append(d.name)
                        break

        inferred_category = _infer_category(guide_id, is_industry)
        inferred_difficulty = _infer_difficulty(guide_id, order)
        origin = _coerce_origin(guide_metadata.get("origin"))
        inferred_kind = GuideKind.CORE
        if origin == GuideOrigin.USER:
            inferred_kind = (
                GuideKind.EXTENSION if guide_metadata.get("base_guide_id") else GuideKind.STANDALONE
            )
        kind = _coerce_kind(guide_metadata.get("kind"), inferred_kind)
        guide_summary = str(
            guide_metadata.get("summary") or guide_metadata.get("description") or ""
        ).strip()
        if not guide_summary:
            guide_summary = next(
                (
                    chapter.summary
                    for chapter in guide_chapters
                    if not chapter.is_glossary and chapter.summary
                ),
                "",
            )
        guide = Guide(
            id=guide_id,
            title=str(
                guide_metadata.get("title")
                or self._guide_titles.get(guide_id)
                or _guide_title_from_dir(guide_id)
            ),
            summary=guide_summary,
            category=_coerce_category(guide_metadata.get("category"), inferred_category),
            difficulty=_coerce_difficulty(guide_metadata.get("difficulty"), inferred_difficulty),
            source_dir=str(guide_dir),
            origin=origin,
            kind=kind,
            owner_user_id=str(guide_metadata.get("owner_user_id") or ""),
            base_guide_id=str(guide_metadata.get("base_guide_id"))
            if guide_metadata.get("base_guide_id")
            else None,
            chapter_count=len(guide_chapters),
            total_word_count=total_words,
            total_reading_time_minutes=reading_time,
            has_glossary=has_glossary,
            prerequisites=prereqs,
            track=track,
        )
        return guide, guide_chapters
