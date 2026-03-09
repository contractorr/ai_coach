"""Shared SQLite helpers ? WAL mode, row_factory defaults, schema versioning."""

import sqlite3
from pathlib import Path


def wal_connect(db_path: str | Path, row_factory: bool = False) -> sqlite3.Connection:
    """Open SQLite connection with WAL journal mode.

    Args:
        db_path: Path to database file.
        row_factory: If True, set conn.row_factory = sqlite3.Row.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    if row_factory:
        conn.row_factory = sqlite3.Row
    return conn


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Read the SQLite user_version pragma for a store."""
    row = conn.execute("PRAGMA user_version").fetchone()
    return int(row[0]) if row else 0


def set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    """Persist the SQLite user_version pragma for a store."""
    conn.execute(f"PRAGMA user_version={int(version)}")


def ensure_schema_version(conn: sqlite3.Connection, version: int) -> int:
    """Ensure a minimum SQLite user_version and return the resulting version."""
    current = get_schema_version(conn)
    if current < version:
        set_schema_version(conn, version)
        return version
    return current
