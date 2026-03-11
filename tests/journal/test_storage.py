"""Tests for journal storage operations."""

import pytest


class TestJournalStorage:
    """Test JournalStorage CRUD operations."""

    def test_create_entry(self, temp_dirs):
        """Test creating a new journal entry."""
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])

        path = storage.create(
            content="Test entry content",
            entry_type="reflection",
            title="Test Title",
            tags=["test", "unit"],
        )

        assert path is not None
        assert (temp_dirs["journal_dir"] / path).exists()

    def test_create_generates_filename(self, temp_dirs):
        """Test that create generates proper filename."""
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])

        path = storage.create(
            content="Test content",
            entry_type="goal",
        )

        assert "goal" in str(path).lower() or str(path).endswith(".md")

    def test_read_entry(self, populated_journal):
        """Test reading an existing entry."""
        storage = populated_journal["storage"]
        path = populated_journal["paths"][0]

        post = storage.read(path)

        assert post is not None
        assert post.content is not None
        assert "reflection" in str(post.metadata.get("type", ""))

    def test_read_nonexistent_raises(self, temp_dirs):
        """Test reading non-existent entry raises FileNotFoundError."""
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])

        with pytest.raises(FileNotFoundError):
            storage.read("nonexistent.md")

    def test_read_rejects_path_outside_journal_dir(self, temp_dirs):
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])
        outside = temp_dirs["journal_dir"].parent / "outside.md"
        outside.write_text("outside", encoding="utf-8")

        with pytest.raises(ValueError, match="Path escapes journal directory"):
            storage.read(outside)

    def test_update_entry(self, populated_journal):
        """Test updating an existing entry."""
        storage = populated_journal["storage"]
        path = populated_journal["paths"][0]

        result = storage.update(path, content="Updated content")

        assert result is not None  # Returns filepath
        post = storage.read(path)
        assert "Updated content" in post.content

    def test_update_rejects_oversized_content(self, populated_journal):
        from journal.storage import MAX_CONTENT_LENGTH

        storage = populated_journal["storage"]
        path = populated_journal["paths"][0]

        with pytest.raises(ValueError, match="Content exceeds max length"):
            storage.update(path, content="x" * (MAX_CONTENT_LENGTH + 1))

    def test_update_rejects_path_outside_journal_dir(self, temp_dirs):
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])
        outside = temp_dirs["journal_dir"].parent / "outside.md"
        outside.write_text("outside", encoding="utf-8")

        with pytest.raises(ValueError, match="Path escapes journal directory"):
            storage.update(outside, content="Updated")

    def test_delete_entry(self, populated_journal):
        """Test deleting an entry."""
        storage = populated_journal["storage"]
        path = populated_journal["paths"][0]

        storage.delete(path)

        with pytest.raises(FileNotFoundError):
            storage.read(path)

    def test_delete_rejects_path_outside_journal_dir(self, temp_dirs):
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])
        outside = temp_dirs["journal_dir"].parent / "outside.md"
        outside.write_text("outside", encoding="utf-8")

        with pytest.raises(ValueError, match="Path escapes journal directory"):
            storage.delete(outside)

    def test_list_entries(self, populated_journal):
        """Test listing all entries."""
        storage = populated_journal["storage"]

        entries = storage.list_entries()

        assert len(entries) >= 3  # At least our sample entries

    def test_list_entries_with_limit(self, populated_journal):
        """Test listing with limit."""
        storage = populated_journal["storage"]

        entries = storage.list_entries(limit=1)

        assert len(entries) == 1

    def test_frontmatter_preserved(self, temp_dirs):
        """Test that YAML frontmatter is preserved."""
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])

        path = storage.create(
            content="Content with metadata",
            entry_type="insight",
            title="Frontmatter Test",
            tags=["meta", "test"],
        )

        post = storage.read(path)

        assert post.metadata.get("type") == "insight"
        assert post.metadata.get("title") == "Frontmatter Test"
        assert "meta" in post.metadata.get("tags", [])

    def test_duplicate_title_handling(self, temp_dirs):
        """Test that duplicate titles create unique files."""
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])

        path1 = storage.create(content="First", entry_type="note", title="Same Title")
        path2 = storage.create(content="Second", entry_type="note", title="Same Title")

        assert path1 != path2
        assert storage.read(path1) is not None
        assert storage.read(path2) is not None

    def test_get_all_content(self, populated_journal):
        """Test getting all content for embedding."""
        storage = populated_journal["storage"]

        entries = storage.get_all_content()

        assert len(entries) >= 3
        for entry in entries:
            assert "id" in entry
            assert "content" in entry
