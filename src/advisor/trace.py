"""Trace entry factory functions for agentic advisor sessions.

Each factory returns a flat dict with ``v``, ``type``, ``ts`` keys plus
type-specific fields.  No I/O — stdlib only.
"""

import time

_VERSION = 1


def make_session_entry(session_id: str, question: str) -> dict:
    return {
        "v": _VERSION,
        "type": "session_start",
        "ts": time.time(),
        "session_id": session_id,
        "question": question,
    }


def make_llm_entry(
    iteration: int,
    finish_reason: str | None,
    tool_call_count: int,
    input_tokens: int = 0,
) -> dict:
    return {
        "v": _VERSION,
        "type": "llm_response",
        "ts": time.time(),
        "iteration": iteration,
        "finish_reason": finish_reason,
        "tool_call_count": tool_call_count,
        "input_tokens": input_tokens,
    }


def make_tool_start_entry(tool_name: str, tool_call_id: str, arg_keys: list[str]) -> dict:
    return {
        "v": _VERSION,
        "type": "tool_start",
        "ts": time.time(),
        "tool": tool_name,
        "tool_call_id": tool_call_id,
        "arg_keys": arg_keys,
    }


def make_tool_done_entry(
    tool_name: str,
    tool_call_id: str,
    chars: int,
    is_error: bool,
) -> dict:
    return {
        "v": _VERSION,
        "type": "tool_done",
        "ts": time.time(),
        "tool": tool_name,
        "tool_call_id": tool_call_id,
        "chars": chars,
        "is_error": is_error,
    }


def make_nudge_entry(used_count: int, min_required: int) -> dict:
    return {
        "v": _VERSION,
        "type": "nudge",
        "ts": time.time(),
        "used_count": used_count,
        "min_required": min_required,
    }


def make_answer_entry(iteration: int, chars: int) -> dict:
    return {
        "v": _VERSION,
        "type": "answer",
        "ts": time.time(),
        "iteration": iteration,
        "chars": chars,
    }


def make_max_iter_entry(max_iterations: int) -> dict:
    return {
        "v": _VERSION,
        "type": "max_iterations_reached",
        "ts": time.time(),
        "max_iterations": max_iterations,
    }
