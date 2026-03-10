"""JSONL persistence for agentic advisor traces."""

import json
import os
import re
from collections.abc import Iterator
from pathlib import Path

_SESSION_ID_RE = re.compile(r"^[0-9a-f]{16,64}$")


class InvalidSessionIdError(ValueError):
    pass


def _validate_session_id(session_id: str) -> None:
    if not _SESSION_ID_RE.match(session_id):
        raise InvalidSessionIdError(f"Invalid session_id: {session_id!r}")


def traces_dir(data_dir: str | Path) -> Path:
    p = Path(data_dir) / "traces"
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_trace(data_dir: str | Path, session_id: str, entries: list[dict]) -> Path:
    _validate_session_id(session_id)
    dest = traces_dir(data_dir) / f"{session_id}.jsonl"
    with open(dest, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    return dest


def list_traces(data_dir: str | Path, limit: int = 20) -> list[dict]:
    d = traces_dir(data_dir)
    files = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    result: list[dict] = []
    for fp in files[:limit]:
        st = fp.stat()
        result.append(
            {
                "session_id": fp.stem,
                "size_bytes": st.st_size,
                "created_at": st.st_mtime,
            }
        )
    return result


def read_trace(data_dir: str | Path, session_id: str, from_line: int = 0) -> Iterator[dict]:
    _validate_session_id(session_id)
    return _read_trace_iter(data_dir, session_id, from_line)


def _read_trace_iter(data_dir: str | Path, session_id: str, from_line: int) -> Iterator[dict]:
    fp = traces_dir(data_dir) / f"{session_id}.jsonl"
    if not fp.exists():
        return
    with open(fp) as f:
        for idx, line in enumerate(f):
            if idx < from_line:
                continue
            line = line.strip()
            if line:
                yield json.loads(line)


def purge_old_traces(data_dir: str | Path, keep: int = 100) -> int:
    d = traces_dir(data_dir)
    files = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    to_delete = files[keep:]
    for fp in to_delete:
        os.remove(fp)
    return len(to_delete)
