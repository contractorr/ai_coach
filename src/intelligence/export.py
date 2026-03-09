"""Intelligence export functionality."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .scraper import IntelStorage


class IntelExporter:
    """Export intelligence items to various formats."""

    def __init__(self, storage: IntelStorage):
        self.storage = storage

    def export_json(
        self,
        output_path: Path,
        days: Optional[int] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> int:
        """Export intel items to JSON.

        Args:
            output_path: Output file path
            days: Only include items from last N days
            source: Filter by source
            limit: Max items to export

        Returns:
            Number of items exported
        """
        items = self._get_items(days, source, limit)

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "count": len(items),
            "items": items,
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)

        return len(items)

    def export_csv(
        self,
        output_path: Path,
        days: Optional[int] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> int:
        """Export intel items to CSV.

        Args:
            output_path: Output file path
            days: Only include items from last N days
            source: Filter by source
            limit: Max items to export

        Returns:
            Number of items exported
        """
        items = self._get_items(days, source, limit)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = ["id", "source", "title", "url", "summary", "published", "scraped_at", "tags"]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for item in items:
                writer.writerow(item)

        return len(items)

    def export_markdown(
        self,
        output_path: Path,
        days: Optional[int] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> int:
        """Export intel items to Markdown.

        Args:
            output_path: Output file path
            days: Only include items from last N days
            source: Filter by source
            limit: Max items to export

        Returns:
            Number of items exported
        """
        items = self._get_items(days, source, limit)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Intelligence Export",
            "",
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Items: {len(items)}",
            "",
            "---",
            "",
        ]

        # Group by source
        by_source: dict[str, list] = {}
        for item in items:
            src = item.get("source", "unknown")
            if src not in by_source:
                by_source[src] = []
            by_source[src].append(item)

        for src, src_items in sorted(by_source.items()):
            lines.append(f"## {src}")
            lines.append("")
            for item in src_items:
                lines.append(f"### [{item['title']}]({item['url']})")
                lines.append("")
                if item.get("summary"):
                    lines.append(item["summary"])
                    lines.append("")
                scraped = item.get("scraped_at", "")[:10] if item.get("scraped_at") else ""
                lines.append(f"*Scraped: {scraped}*")
                lines.append("")
            lines.append("---")
            lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return len(items)

    def _get_items(
        self,
        days: Optional[int] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Get filtered intel items."""
        items = self.storage.get_recent(
            days=days or 365,
            limit=limit or 10000,
        )

        if source:
            items = [i for i in items if i.get("source") == source]

        return items
