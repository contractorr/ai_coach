"""Lifecycle and schema version tests for persisted stores."""

from db import get_schema_version, wal_connect
from intelligence.scraper import SCHEMA_VERSION as INTEL_SCHEMA_VERSION
from intelligence.scraper import IntelStorage
from journal.storage import STORE_VERSION as JOURNAL_STORE_VERSION
from journal.storage import JournalStorage
from memory.store import SCHEMA_VERSION as MEMORY_SCHEMA_VERSION
from memory.store import FactStore


def test_fact_store_sets_schema_version(tmp_path):
    db_path = tmp_path / "memory.db"
    FactStore(db_path, chroma_dir=None)

    with wal_connect(db_path) as conn:
        assert get_schema_version(conn) == MEMORY_SCHEMA_VERSION


def test_intel_store_sets_schema_version(tmp_path):
    db_path = tmp_path / "intel.db"
    IntelStorage(db_path)

    with wal_connect(db_path) as conn:
        assert get_schema_version(conn) == INTEL_SCHEMA_VERSION


def test_journal_storage_writes_metadata_marker(tmp_path):
    storage = JournalStorage(tmp_path / "journal")

    metadata = storage.get_store_metadata()

    assert metadata == {"store": "journal", "version": JOURNAL_STORE_VERSION}
