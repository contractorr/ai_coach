"""Markdown journal CRUD operations."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import frontmatter

from shared_types import EntryType

ALLOWED_ENTRY_TYPES = tuple(EntryType)
MAX_CONTENT_LENGTH = 100_000  # 100KB
MAX_TAG_LENGTH = 50
MAX_TAGS = 20
STORE_VERSION = 1
STORE_META_FILENAME = ".stewardme-journal.json"


def _sanitize_slug(text: str) -> str:
    """Sanitize text into safe filename slug. Only [a-z0-9-] allowed."""
    slug = text.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    return slug[:50]


def _sanitize_tag(tag: str) -> str:
    """Sanitize a single tag."""
    return re.sub(r"[^\w\s-]", "", tag).strip()[:MAX_TAG_LENGTH]


class JournalStorage:
    """Manages markdown journal files with YAML frontmatter."""

    def __init__(self, journal_dir: str | Path):
        self.journal_dir = Path(journal_dir).expanduser().resolve()
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        self._init_store_metadata()

    def _init_store_metadata(self) -> None:
        """Ensure a simple metadata marker exists for the journal store."""
        metadata_path = self.journal_dir / STORE_META_FILENAME
        if metadata_path.exists():
            return
        metadata_path.write_text(
            json.dumps({"store": "journal", "version": STORE_VERSION}, indent=2),
            encoding="utf-8",
        )

    def get_store_metadata(self) -> dict:
        """Read the journal store metadata marker."""
        metadata_path = self.journal_dir / STORE_META_FILENAME
        return json.loads(metadata_path.read_text(encoding="utf-8"))

    def _generate_filename(self, entry_type: str, title: str) -> str:
        """Generate filename from type, date, and title."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        slug = _sanitize_slug(title)
        safe_type = _sanitize_slug(entry_type)
        return f"{date_str}_{safe_type}_{slug}.md"

    def _validate_path(self, filepath: Path) -> Path:
        """Ensure resolved path is inside journal_dir."""
        resolved = filepath.resolve()
        if not resolved.is_relative_to(self.journal_dir):
            raise ValueError(f"Path escapes journal directory: {filepath}")
        return resolved

    def _resolve_entry_path(self, filepath: str | Path) -> Path:
        """Resolve an entry path relative to journal_dir and enforce containment."""
        path = Path(filepath)
        if not path.is_absolute():
            path = self.journal_dir / path
        return self._validate_path(path)

    @staticmethod
    def _validate_content(content: str) -> None:
        if len(content) > MAX_CONTENT_LENGTH:
            raise ValueError(f"Content exceeds max length ({MAX_CONTENT_LENGTH} chars)")

    def create(
        self,
        content: str,
        entry_type: str = "daily",
        title: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ) -> Path:
        """Create new journal entry.

        Args:
            content: Main body text
            entry_type: daily, project, goal, reflection
            title: Optional title (defaults to date)
            tags: Optional list of tags
            metadata: Additional frontmatter fields

        Returns:
            Path to created file

        Raises:
            ValueError: If entry_type invalid, content too long, or path escapes journal dir
        """
        if entry_type not in ALLOWED_ENTRY_TYPES:
            raise ValueError(
                f"Invalid entry_type '{entry_type}'. Must be one of {ALLOWED_ENTRY_TYPES}"
            )

        self._validate_content(content)

        now = datetime.now()
        title = title or now.strftime("%B %d, %Y")

        # Sanitize tags
        if tags:
            tags = [_sanitize_tag(t) for t in tags[:MAX_TAGS] if t.strip()]

        fm = frontmatter.Post(content)
        fm["title"] = title
        fm["type"] = entry_type
        fm["created"] = now.isoformat()
        fm["tags"] = tags or []

        if metadata:
            for k, v in metadata.items():
                fm[k] = v

        filename = self._generate_filename(entry_type, title)
        filepath = self._validate_path(self.journal_dir / filename)

        # Handle duplicates
        counter = 1
        while filepath.exists():
            base = filename.rsplit(".", 1)[0]
            filepath = self._validate_path(self.journal_dir / f"{base}_{counter}.md")
            counter += 1

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(fm))

        return filepath

    def read(self, filepath: str | Path) -> frontmatter.Post:
        """Read journal entry."""
        return frontmatter.load(self._resolve_entry_path(filepath))

    def update(
        self,
        filepath: str | Path,
        content: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Path:
        """Update existing entry."""
        filepath = self._resolve_entry_path(filepath)
        post = frontmatter.load(filepath)

        if content is not None:
            self._validate_content(content)
            post.content = content

        if metadata:
            for k, v in metadata.items():
                post[k] = v

        post["updated"] = datetime.now().isoformat()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        return filepath

    def delete(self, filepath: str | Path) -> bool:
        """Delete journal entry."""
        filepath = self._resolve_entry_path(filepath)
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def list_entries(
        self,
        entry_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 50,
    ) -> list[dict]:
        """List journal entries with optional filtering."""
        entries = []

        for f in sorted(self.journal_dir.glob("*.md"), reverse=True):
            try:
                post = frontmatter.load(f)
                entry = {
                    "path": f,
                    "title": post.get("title", f.stem),
                    "type": post.get("type", "unknown"),
                    "created": post.get("created"),
                    "tags": post.get("tags", []),
                    "preview": post.content[:200] if post.content else "",
                }

                # Filter by type
                if entry_type and entry["type"] != entry_type:
                    continue

                # Filter by tags
                if tags and not any(t in entry["tags"] for t in tags):
                    continue

                entries.append(entry)

                if len(entries) >= limit:
                    break

            except (OSError, ValueError):
                continue

        return entries

    def get_all_content(self) -> list[dict]:
        """Get all entries with full content for embedding."""
        entries = []
        for f in self.journal_dir.glob("*.md"):
            try:
                post = frontmatter.load(f)
                entries.append(
                    {
                        "id": str(f),
                        "content": post.content,
                        "metadata": dict(post.metadata),
                    }
                )
            except (OSError, ValueError):
                continue
        return entries
