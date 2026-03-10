"""Tests for trace_store: JSONL roundtrip, list, purge, path traversal."""

import json

import pytest

from advisor.trace_store import (
    InvalidSessionIdError,
    list_traces,
    purge_old_traces,
    read_trace,
    write_trace,
)


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "userdata"


def _sample_entries(n=3):
    return [{"v": 1, "type": f"entry_{i}", "ts": 1000.0 + i} for i in range(n)]


class TestWriteRead:
    def test_roundtrip(self, data_dir):
        entries = _sample_entries()
        path = write_trace(data_dir, "abcdef1234567890", entries)
        assert path.exists()
        result = list(read_trace(data_dir, "abcdef1234567890"))
        assert result == entries

    def test_jsonl_format(self, data_dir):
        entries = _sample_entries(2)
        path = write_trace(data_dir, "abcdef1234567890", entries)
        lines = path.read_text().strip().splitlines()
        assert len(lines) == 2
        for line in lines:
            json.loads(line)  # must be valid JSON

    def test_from_line_offset(self, data_dir):
        entries = _sample_entries(5)
        write_trace(data_dir, "abcdef1234567890", entries)
        result = list(read_trace(data_dir, "abcdef1234567890", from_line=3))
        assert len(result) == 2
        assert result[0] == entries[3]
        assert result[1] == entries[4]

    def test_read_nonexistent_returns_empty(self, data_dir):
        result = list(read_trace(data_dir, "0000000000000000"))
        assert result == []


class TestListTraces:
    def test_empty_dir(self, data_dir):
        assert list_traces(data_dir) == []

    def test_ordering_newest_first(self, data_dir):
        import time

        write_trace(data_dir, "aaaa000000000001", [{"v": 1}])
        time.sleep(0.05)
        write_trace(data_dir, "bbbb000000000002", [{"v": 1}])

        result = list_traces(data_dir)
        assert len(result) == 2
        assert result[0]["session_id"] == "bbbb000000000002"
        assert result[1]["session_id"] == "aaaa000000000001"

    def test_limit(self, data_dir):
        for i in range(5):
            write_trace(data_dir, f"{'%016x' % i}", [{"v": 1}])
        result = list_traces(data_dir, limit=2)
        assert len(result) == 2

    def test_includes_size_bytes(self, data_dir):
        write_trace(data_dir, "abcdef1234567890", _sample_entries(3))
        result = list_traces(data_dir)
        assert result[0]["size_bytes"] > 0


class TestPurge:
    def test_purge_keeps_newest(self, data_dir):
        import time

        ids = []
        for i in range(5):
            sid = f"{'%016x' % i}"
            ids.append(sid)
            write_trace(data_dir, sid, [{"v": 1}])
            time.sleep(0.02)

        deleted = purge_old_traces(data_dir, keep=2)
        assert deleted == 3
        remaining = list_traces(data_dir)
        assert len(remaining) == 2

    def test_purge_nothing_when_under_limit(self, data_dir):
        write_trace(data_dir, "abcdef1234567890", [{"v": 1}])
        deleted = purge_old_traces(data_dir, keep=10)
        assert deleted == 0


class TestPathTraversal:
    def test_reject_dotdot(self, data_dir):
        with pytest.raises(InvalidSessionIdError):
            write_trace(data_dir, "../etc/passwd", [])

    def test_reject_slash(self, data_dir):
        with pytest.raises(InvalidSessionIdError):
            read_trace(data_dir, "abcdef12/34567890")

    def test_reject_non_hex(self, data_dir):
        with pytest.raises(InvalidSessionIdError):
            write_trace(data_dir, "ZZZZ0000000000", [])

    def test_reject_too_short(self, data_dir):
        with pytest.raises(InvalidSessionIdError):
            write_trace(data_dir, "abc", [])
