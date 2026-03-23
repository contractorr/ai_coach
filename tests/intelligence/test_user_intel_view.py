"""Tests for UserIntelView — user-scoped intel filtering."""

import pytest

from intelligence.scraper import IntelItem, IntelStorage
from intelligence.user_intel_view import UserIntelView


@pytest.fixture
def storage(temp_dirs):
    """Populated IntelStorage with shared + user-specific items."""
    s = IntelStorage(temp_dirs["intel_db"])
    # Shared items (user_id=None)
    s.save(IntelItem(source="hn", title="Shared HN Post", url="https://a.com/1", summary="shared"))
    s.save(IntelItem(source="rss", title="Shared RSS", url="https://a.com/2", summary="shared rss"))
    # User A items
    s.save(
        IntelItem(
            source="rss",
            title="User A Feed",
            url="https://a.com/3",
            summary="user a",
            user_id="alice",
        )
    )
    # User B items
    s.save(
        IntelItem(
            source="rss",
            title="User B Feed",
            url="https://a.com/4",
            summary="user b",
            user_id="bob",
        )
    )
    return s


class TestUserIntelView:
    def test_no_user_sees_all(self, storage):
        """user_id=None returns all items (CLI compat)."""
        view = UserIntelView(storage, user_id=None)
        items = view.get_recent(days=7, limit=100)
        assert len(items) == 4

    def test_user_a_sees_shared_plus_own(self, storage):
        view = UserIntelView(storage, user_id="alice")
        items = view.get_recent(days=7, limit=100)
        urls = {i["url"] for i in items}
        assert "https://a.com/1" in urls  # shared
        assert "https://a.com/2" in urls  # shared
        assert "https://a.com/3" in urls  # alice's
        assert "https://a.com/4" not in urls  # bob's

    def test_user_b_sees_shared_plus_own(self, storage):
        view = UserIntelView(storage, user_id="bob")
        items = view.get_recent(days=7, limit=100)
        urls = {i["url"] for i in items}
        assert "https://a.com/1" in urls
        assert "https://a.com/2" in urls
        assert "https://a.com/3" not in urls  # alice's
        assert "https://a.com/4" in urls  # bob's

    def test_search_filters_by_user(self, storage):
        view = UserIntelView(storage, user_id="alice")
        items = view.search("Feed")
        titles = {i["title"] for i in items}
        assert "User A Feed" in titles
        assert "User B Feed" not in titles

    def test_fts_search_filters_by_user(self, storage):
        view = UserIntelView(storage, user_id="bob")
        items = view.fts_search("Feed")
        titles = {i["title"] for i in items}
        assert "User B Feed" in titles
        assert "User A Feed" not in titles

    def test_get_items_since_filters(self, storage):
        from datetime import datetime, timedelta

        view = UserIntelView(storage, user_id="alice")
        items = view.get_items_since(datetime.now() - timedelta(days=1))
        urls = {i["url"] for i in items}
        assert "https://a.com/4" not in urls  # bob's

    def test_get_by_date_range_filters(self, storage):
        view = UserIntelView(storage, user_id="bob")
        items = view.get_by_date_range()
        urls = {i["url"] for i in items}
        assert "https://a.com/3" not in urls  # alice's
        assert "https://a.com/4" in urls

    def test_write_through(self, storage):
        """Write methods delegate to underlying storage unchanged."""
        view = UserIntelView(storage, user_id="alice")
        item = IntelItem(source="test", title="New", url="https://a.com/new", summary="new item")
        row_id = view.save(item)
        assert row_id is not None

    def test_db_path_matches_storage(self, storage):
        view = UserIntelView(storage, user_id="alice")
        assert view.db_path == storage.db_path


class TestUserIdOnIntelItem:
    def test_user_id_defaults_none(self):
        item = IntelItem(source="test", title="T", url="https://x.com", summary="s")
        assert item.user_id is None

    def test_user_id_saved_and_retrieved(self, temp_dirs):
        s = IntelStorage(temp_dirs["intel_db"])
        item = IntelItem(
            source="test", title="User Item", url="https://x.com/u", summary="s", user_id="user1"
        )
        row_id = s.save(item)
        assert row_id
        retrieved = s.get_item_by_id(row_id)
        assert retrieved["user_id"] == "user1"

    def test_shared_item_has_null_user_id(self, temp_dirs):
        s = IntelStorage(temp_dirs["intel_db"])
        item = IntelItem(source="test", title="Shared", url="https://x.com/s", summary="s")
        row_id = s.save(item)
        assert row_id
        retrieved = s.get_item_by_id(row_id)
        assert retrieved["user_id"] is None
