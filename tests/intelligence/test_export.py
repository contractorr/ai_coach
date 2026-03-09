"""Tests for intelligence export functionality."""

import csv
import json
from datetime import datetime

import pytest

from intelligence.export import IntelExporter
from intelligence.scraper import IntelItem, IntelStorage


@pytest.fixture
def intel_setup(tmp_path):
    db = tmp_path / "intel.db"
    storage = IntelStorage(db)

    items = [
        IntelItem(
            source="hackernews",
            title="HN Story",
            url="https://example.com/hn1",
            summary="100 points",
            published=datetime.now(),
            tags=["ai"],
        ),
        IntelItem(
            source="reddit:startups",
            title="Reddit Post",
            url="https://reddit.com/r/startups/1",
            summary="50 pts",
            published=datetime.now(),
            tags=["startup"],
        ),
        IntelItem(
            source="hackernews",
            title="Another HN",
            url="https://example.com/hn2",
            summary="200 points",
            published=datetime.now(),
            tags=["rust"],
        ),
    ]
    for item in items:
        storage.save(item)

    exporter = IntelExporter(storage)
    return {"exporter": exporter, "storage": storage, "tmp": tmp_path}


class TestIntelExportJSON:
    def test_export_json_all(self, intel_setup):
        out = intel_setup["tmp"] / "intel.json"
        count = intel_setup["exporter"].export_json(out)
        assert count == 3
        data = json.loads(out.read_text())
        assert data["count"] == 3
        assert len(data["items"]) == 3

    def test_export_json_filter_source(self, intel_setup):
        out = intel_setup["tmp"] / "hn.json"
        count = intel_setup["exporter"].export_json(out, source="hackernews")
        assert count == 2

    def test_export_json_limit(self, intel_setup):
        out = intel_setup["tmp"] / "limited.json"
        count = intel_setup["exporter"].export_json(out, limit=1)
        assert count == 1


class TestIntelExportCSV:
    def test_export_csv_all(self, intel_setup):
        out = intel_setup["tmp"] / "intel.csv"
        count = intel_setup["exporter"].export_csv(out)
        assert count == 3
        assert out.exists()

        with open(out) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 3
        assert "source" in rows[0]
        assert "title" in rows[0]

    def test_export_csv_filter_source(self, intel_setup):
        out = intel_setup["tmp"] / "reddit.csv"
        count = intel_setup["exporter"].export_csv(out, source="reddit:startups")
        assert count == 1


class TestIntelExportMarkdown:
    def test_export_markdown_all(self, intel_setup):
        out = intel_setup["tmp"] / "intel.md"
        count = intel_setup["exporter"].export_markdown(out)
        assert count == 3

        content = out.read_text()
        assert "# Intelligence Export" in content
        assert "hackernews" in content
        assert "HN Story" in content

    def test_export_markdown_groups_by_source(self, intel_setup):
        out = intel_setup["tmp"] / "grouped.md"
        intel_setup["exporter"].export_markdown(out)
        content = out.read_text()
        # Should have source headers
        assert "## hackernews" in content
        assert "## reddit:startups" in content

    def test_export_empty(self, tmp_path):
        db = tmp_path / "empty.db"
        storage = IntelStorage(db)
        exporter = IntelExporter(storage)

        out = tmp_path / "empty.json"
        count = exporter.export_json(out)
        assert count == 0

    def test_export_unicode(self, tmp_path):
        db = tmp_path / "unicode.db"
        storage = IntelStorage(db)
        storage.save(
            IntelItem(
                source="hackernews",
                title="Unicode: caf\u00e9 \u2603",
                url="https://example.com/unicode",
                summary="test",
            )
        )
        exporter = IntelExporter(storage)
        out = tmp_path / "unicode.md"
        count = exporter.export_markdown(out)
        assert count == 1
        assert "\u2603" in out.read_text(encoding="utf-8")
