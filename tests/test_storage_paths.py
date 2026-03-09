"""Tests for canonical user path resolution."""

from storage_paths import get_single_user_paths, get_user_paths


def test_get_user_paths_returns_canonical_user_and_shared_paths(tmp_path):
    paths = get_user_paths("google:123", coach_home=tmp_path)

    user_dir = tmp_path / "users" / "google_123"
    assert paths["data_dir"] == user_dir
    assert paths["journal_dir"] == user_dir / "journal"
    assert paths["journal_dir"].exists()
    assert paths["profile"] == user_dir / "profile.yaml"
    assert paths["profile_path"] == user_dir / "profile.yaml"
    assert paths["memory_db"] == user_dir / "memory.db"
    assert paths["threads_db"] == user_dir / "threads.db"
    assert paths["watchlist_path"] == user_dir / "watchlist.json"
    assert paths["follow_up_path"] == user_dir / "intel_follow_ups.json"
    assert paths["intel_follow_ups_path"] == user_dir / "intel_follow_ups.json"
    assert paths["intel_db"] == tmp_path / "intel.db"


def test_get_single_user_paths_returns_rooted_local_paths(tmp_path):
    profile_path = tmp_path / "custom" / "profile.yaml"
    paths = get_single_user_paths(coach_home=tmp_path, profile_path=profile_path)

    assert paths["data_dir"] == tmp_path
    assert paths["journal_dir"] == tmp_path / "journal"
    assert paths["journal_dir"].exists()
    assert paths["profile"] == profile_path
    assert paths["profile_path"] == profile_path
    assert paths["memory_db"] == tmp_path / "memory.db"
    assert paths["threads_db"] == tmp_path / "threads.db"
    assert paths["watchlist_path"] == tmp_path / "watchlist.json"
    assert paths["follow_up_path"] == tmp_path / "intel_follow_ups.json"
    assert paths["intel_db"] == tmp_path / "intel.db"
