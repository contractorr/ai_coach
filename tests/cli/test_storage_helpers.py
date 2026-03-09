"""Tests for canonical CLI storage helpers."""

from cli.utils import (
    get_insight_store,
    get_intel_storage,
    get_memory_store,
    get_profile_path,
    get_rec_db_path,
    get_recommendation_storage,
    get_storage_paths,
)


def test_get_storage_paths_uses_intel_db_parent_as_single_user_root(tmp_path):
    config = {
        "paths": {
            "journal_dir": str(tmp_path / "journal"),
            "chroma_dir": str(tmp_path / "chroma"),
            "intel_db": str(tmp_path / "intel.db"),
        },
        "profile": {"path": str(tmp_path / "custom-profile.yaml")},
    }
    paths = {
        "journal_dir": tmp_path / "journal",
        "chroma_dir": tmp_path / "chroma",
        "intel_db": tmp_path / "intel.db",
    }

    storage_paths = get_storage_paths(config=config, paths=paths)

    assert storage_paths["data_dir"] == tmp_path
    assert storage_paths["journal_dir"] == tmp_path / "journal"
    assert storage_paths["memory_db"] == tmp_path / "memory.db"
    assert storage_paths["threads_db"] == tmp_path / "threads.db"
    assert storage_paths["watchlist_path"] == tmp_path / "watchlist.json"
    assert storage_paths["recommendations_dir"] == tmp_path / "recommendations"
    assert storage_paths["profile_path"] == tmp_path / "custom-profile.yaml"


def test_cli_path_helpers_delegate_to_canonical_storage_paths(tmp_path):
    config = {
        "paths": {
            "journal_dir": str(tmp_path / "journal"),
            "chroma_dir": str(tmp_path / "chroma"),
            "intel_db": str(tmp_path / "intel.db"),
        },
        "profile": {"path": str(tmp_path / "profile.yaml")},
    }
    storage_paths = {
        "recommendations_dir": tmp_path / "recommendations",
        "profile_path": tmp_path / "profile.yaml",
    }

    assert get_rec_db_path(config, storage_paths=storage_paths) == tmp_path / "recommendations"
    assert get_profile_path(config, storage_paths=storage_paths) == str(tmp_path / "profile.yaml")


def test_cli_storage_helpers_build_shared_stores(tmp_path):
    config = {
        "paths": {
            "journal_dir": str(tmp_path / "journal"),
            "chroma_dir": str(tmp_path / "chroma"),
            "intel_db": str(tmp_path / "intel.db"),
        },
        "profile": {"path": str(tmp_path / "profile.yaml")},
    }
    storage_paths = get_storage_paths(
        config=config,
        paths={
            "journal_dir": tmp_path / "journal",
            "chroma_dir": tmp_path / "chroma",
            "intel_db": tmp_path / "intel.db",
        },
    )

    assert get_memory_store(config, storage_paths=storage_paths).db_path == tmp_path / "memory.db"
    assert get_intel_storage(config, storage_paths=storage_paths).db_path == tmp_path / "intel.db"
    assert (
        get_recommendation_storage(config, storage_paths=storage_paths).dir
        == tmp_path / "recommendations"
    )
    assert get_insight_store(config, storage_paths=storage_paths).db_path == tmp_path / "intel.db"
