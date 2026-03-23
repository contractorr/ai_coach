"""Shared path helpers for user-scoped and single-user storage."""

import os
from pathlib import Path
from typing import TypedDict


class StoragePaths(TypedDict):
    """Canonical storage path dictionary (18 keys) returned by path builders."""

    data_dir: Path
    journal_dir: Path
    chroma_dir: Path
    recommendations_dir: Path
    profile: Path  # legacy alias
    profile_path: Path  # canonical
    memory_db: Path
    threads_db: Path
    receipts_db: Path
    mind_maps_db: Path
    escalations_db: Path
    outcomes_db: Path
    assumptions_db: Path
    watchlist_path: Path
    follow_up_path: Path  # legacy alias
    intel_follow_ups_path: Path  # canonical
    intel_db: Path


def get_coach_home(coach_home: Path | None = None) -> Path:
    """Return the base coach directory."""
    if coach_home is not None:
        return coach_home

    env_home = os.getenv("COACH_HOME")
    if env_home:
        return Path(env_home).expanduser()

    return Path.home() / "coach"


def safe_user_id(user_id: str) -> str:
    """Sanitize a user ID for file paths and collection names."""
    return user_id.replace(":", "_")


def _build_paths(data_dir: Path, profile_path: Path, intel_db: Path) -> StoragePaths:
    """Build a canonical path dictionary for an already-chosen data directory."""
    data_dir.mkdir(parents=True, exist_ok=True)

    journal_dir = data_dir / "journal"
    journal_dir.mkdir(exist_ok=True)

    follow_up_path = data_dir / "intel_follow_ups.json"
    return StoragePaths(
        data_dir=data_dir,
        journal_dir=journal_dir,
        chroma_dir=data_dir / "chroma",
        recommendations_dir=data_dir / "recommendations",
        profile=profile_path,
        profile_path=profile_path,
        memory_db=data_dir / "memory.db",
        threads_db=data_dir / "threads.db",
        receipts_db=data_dir / "receipts.db",
        mind_maps_db=data_dir / "mind_maps.db",
        escalations_db=data_dir / "escalations.db",
        outcomes_db=data_dir / "outcomes.db",
        assumptions_db=data_dir / "assumptions.db",
        watchlist_path=data_dir / "watchlist.json",
        follow_up_path=follow_up_path,
        intel_follow_ups_path=follow_up_path,
        intel_db=intel_db,
    )


def get_user_paths(user_id: str, coach_home: Path | None = None) -> StoragePaths:
    """Return canonical per-user paths plus shared intel path."""
    base_home = get_coach_home(coach_home)
    data_dir = base_home / "users" / safe_user_id(user_id)
    profile_path = data_dir / "profile.yaml"
    return _build_paths(data_dir, profile_path, base_home / "intel.db")


def get_single_user_paths(
    coach_home: Path | None = None,
    profile_path: Path | None = None,
) -> StoragePaths:
    """Return canonical single-user local paths rooted at the coach home directory."""
    base_home = get_coach_home(coach_home)
    resolved_profile = profile_path or (base_home / "profile.yaml")
    return _build_paths(base_home, resolved_profile, base_home / "intel.db")
