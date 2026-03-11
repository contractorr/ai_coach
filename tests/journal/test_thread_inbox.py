"""Tests for thread inbox overlay state."""

from journal.thread_inbox import ThreadInboxStateStore


class TestThreadInboxStateStore:
    def test_upsert_preserves_links_when_fields_are_omitted(self, tmp_path):
        store = ThreadInboxStateStore(tmp_path / "threads.db")

        store.upsert_state(
            "thread-1",
            inbox_state="goal_created",
            linked_goal_path="goal.md",
            linked_dossier_id="dossier-1",
        )
        state = store.upsert_state("thread-1", inbox_state="active")

        assert state["linked_goal_path"] == "goal.md"
        assert state["linked_dossier_id"] == "dossier-1"

    def test_upsert_can_clear_goal_and_dossier_links(self, tmp_path):
        store = ThreadInboxStateStore(tmp_path / "threads.db")

        store.upsert_state(
            "thread-1",
            inbox_state="goal_created",
            linked_goal_path="goal.md",
            linked_dossier_id="dossier-1",
        )
        state = store.upsert_state(
            "thread-1",
            inbox_state="active",
            linked_goal_path=None,
            linked_dossier_id=None,
        )

        assert state["linked_goal_path"] is None
        assert state["linked_dossier_id"] is None
