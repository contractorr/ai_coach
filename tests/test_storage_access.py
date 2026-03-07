"""Tests for shared storage constructors."""

from storage_access import (
    create_follow_up_store,
    create_goal_intel_match_store,
    create_insight_store,
    create_intel_storage,
    create_memory_store,
    create_profile_storage,
    create_recommendation_storage,
    create_thread_store,
    create_watchlist_store,
    get_profile_path,
    get_recommendations_dir,
)


def test_storage_access_builds_stores_from_canonical_paths(tmp_path):
    paths = {
        "profile_path": tmp_path / "profile.yaml",
        "memory_db": tmp_path / "memory.db",
        "threads_db": tmp_path / "threads.db",
        "watchlist_path": tmp_path / "watchlist.json",
        "follow_up_path": tmp_path / "intel_follow_ups.json",
        "recommendations_dir": tmp_path / "recommendations",
        "intel_db": tmp_path / "intel.db",
        "chroma_dir": tmp_path / "chroma",
    }

    profile_storage = create_profile_storage(paths)
    memory_store = create_memory_store(paths)
    thread_store = create_thread_store(paths)
    watchlist_store = create_watchlist_store(paths)
    follow_up_store = create_follow_up_store(paths)
    intel_storage = create_intel_storage(paths)
    recommendation_storage = create_recommendation_storage(paths)
    insight_store = create_insight_store(paths)
    goal_match_store = create_goal_intel_match_store(paths)

    assert profile_storage.path == tmp_path / "profile.yaml"
    assert memory_store.db_path == tmp_path / "memory.db"
    assert thread_store.db_path == tmp_path / "threads.db"
    assert watchlist_store.path == tmp_path / "watchlist.json"
    assert follow_up_store.path == tmp_path / "intel_follow_ups.json"
    assert intel_storage.db_path == tmp_path / "intel.db"
    assert recommendation_storage.dir == tmp_path / "recommendations"
    assert insight_store.db_path == tmp_path / "intel.db"
    assert goal_match_store.db_path == tmp_path / "intel.db"
    assert get_recommendations_dir(paths) == tmp_path / "recommendations"


def test_storage_access_accepts_legacy_profile_key(tmp_path):
    paths = {
        "profile": tmp_path / "legacy-profile.yaml",
        "recommendations_dir": tmp_path / "recommendations",
    }

    assert get_profile_path(paths) == tmp_path / "legacy-profile.yaml"
