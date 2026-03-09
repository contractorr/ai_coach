"""Tests for journal export functionality."""

import json

import pytest

from journal.export import JournalExporter
from journal.storage import JournalStorage


@pytest.fixture
def exporter_setup(tmp_path):
    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()
    storage = JournalStorage(journal_dir)

    # Create test entries
    storage.create(content="Entry one content", entry_type="daily", title="Day One", tags=["work"])
    storage.create(
        content="Entry two content", entry_type="goal", title="Learn Rust", tags=["learning"]
    )
    storage.create(
        content="Third entry", entry_type="reflection", title="Week Review", tags=["review"]
    )

    exporter = JournalExporter(storage)
    return {"exporter": exporter, "storage": storage, "tmp": tmp_path}


class TestJournalExportJSON:
    def test_export_json_all(self, exporter_setup):
        out = exporter_setup["tmp"] / "export.json"
        count = exporter_setup["exporter"].export_json(out)
        assert count == 3
        assert out.exists()

        data = json.loads(out.read_text())
        assert data["count"] == 3
        assert len(data["entries"]) == 3
        assert "exported_at" in data

    def test_export_json_filter_type(self, exporter_setup):
        out = exporter_setup["tmp"] / "goals.json"
        count = exporter_setup["exporter"].export_json(out, entry_type="goal")
        assert count == 1

        data = json.loads(out.read_text())
        assert data["entries"][0]["type"] == "goal"

    def test_export_json_limit(self, exporter_setup):
        out = exporter_setup["tmp"] / "limited.json"
        count = exporter_setup["exporter"].export_json(out, limit=2)
        assert count == 2

    def test_export_json_creates_parent_dirs(self, exporter_setup):
        out = exporter_setup["tmp"] / "sub" / "dir" / "export.json"
        count = exporter_setup["exporter"].export_json(out)
        assert count == 3
        assert out.exists()

    def test_export_json_empty(self, tmp_path):
        journal_dir = tmp_path / "empty_journal"
        journal_dir.mkdir()
        storage = JournalStorage(journal_dir)
        exporter = JournalExporter(storage)

        out = tmp_path / "empty.json"
        count = exporter.export_json(out)
        assert count == 0
        data = json.loads(out.read_text())
        assert data["entries"] == []


class TestJournalExportMarkdown:
    def test_export_markdown_all(self, exporter_setup):
        out = exporter_setup["tmp"] / "export.md"
        count = exporter_setup["exporter"].export_markdown(out)
        assert count == 3
        assert out.exists()

        content = out.read_text()
        assert "# Journal Export" in content
        assert "Day One" in content
        assert "Learn Rust" in content

    def test_export_markdown_filter_type(self, exporter_setup):
        out = exporter_setup["tmp"] / "reflections.md"
        count = exporter_setup["exporter"].export_markdown(out, entry_type="reflection")
        assert count == 1

        content = out.read_text()
        assert "Week Review" in content

    def test_export_markdown_unicode(self, tmp_path):
        journal_dir = tmp_path / "unicode_journal"
        journal_dir.mkdir()
        storage = JournalStorage(journal_dir)
        storage.create(
            content="Content with unicode: cafe\u0301 \u2603 \u2764",
            entry_type="daily",
            title="Unicode Test",
        )

        exporter = JournalExporter(storage)
        out = tmp_path / "unicode.md"
        count = exporter.export_markdown(out)
        assert count == 1
        content = out.read_text(encoding="utf-8")
        assert "\u2603" in content
