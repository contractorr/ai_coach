"""Journal export functionality."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .storage import JournalStorage


class JournalExporter:
    """Export journal entries to various formats."""

    def __init__(self, storage: JournalStorage):
        self.storage = storage

    def export_json(
        self,
        output_path: Path,
        entry_type: Optional[str] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> int:
        """Export entries to JSON.

        Args:
            output_path: Output file path
            entry_type: Filter by type
            days: Only include entries from last N days
            limit: Max entries to export

        Returns:
            Number of entries exported
        """
        entries = self._get_entries(entry_type, days, limit)

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "count": len(entries),
            "entries": entries,
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)

        return len(entries)

    def export_markdown(
        self,
        output_path: Path,
        entry_type: Optional[str] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> int:
        """Export entries to Markdown.

        Args:
            output_path: Output file path
            entry_type: Filter by type
            days: Only include entries from last N days
            limit: Max entries to export

        Returns:
            Number of entries exported
        """
        entries = self._get_entries(entry_type, days, limit)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Journal Export",
            "",
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Entries: {len(entries)}",
            "",
            "---",
            "",
        ]

        for entry in entries:
            lines.append(f"## {entry['title']}")
            lines.append("")
            lines.append(
                f"**Type:** {entry['type']} | **Date:** {entry['created'][:10] if entry.get('created') else 'N/A'}"
            )
            if entry.get("tags"):
                lines.append(f"**Tags:** {', '.join(entry['tags'])}")
            lines.append("")
            lines.append(entry.get("content", ""))
            lines.append("")
            lines.append("---")
            lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return len(entries)

    def _get_entries(
        self,
        entry_type: Optional[str] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Get filtered entries with content."""
        entries = self.storage.list_entries(
            entry_type=entry_type,
            limit=limit or 1000,
        )

        # Filter by days if specified
        if days:
            from datetime import timedelta

            cutoff = datetime.now() - timedelta(days=days)
            filtered = []
            for e in entries:
                created = e.get("created")
                if created:
                    try:
                        entry_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        if entry_date.replace(tzinfo=None) >= cutoff:
                            filtered.append(e)
                    except ValueError:
                        filtered.append(e)
                else:
                    filtered.append(e)
            entries = filtered

        # Load full content for each entry
        result = []
        for entry in entries:
            try:
                post = self.storage.read(entry["path"])
                result.append(
                    {
                        "title": entry["title"],
                        "type": entry["type"],
                        "created": entry.get("created"),
                        "tags": entry.get("tags", []),
                        "content": post.content,
                    }
                )
            except (OSError, ValueError):
                continue

        return result
