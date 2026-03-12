"""Shared advisor/advice orchestration helpers."""

import time
from pathlib import Path
from typing import Any, Callable

import structlog

logger = structlog.get_logger()

DEFAULT_MAX_HISTORY_CHARS = 64_000


class ConversationNotFoundError(Exception):
    """Raised when a conversation does not belong to the current user."""


def trim_history(messages: list[dict], max_chars: int = DEFAULT_MAX_HISTORY_CHARS) -> list[dict]:
    """Keep the most recent messages that fit within a character budget."""
    total = 0
    trimmed = []
    for msg in reversed(messages):
        total += len(msg.get("content", ""))
        if total > max_chars:
            break
        trimmed.append(msg)
    trimmed.reverse()
    return trimmed


def start_conversation_turn(
    *,
    user_id: str,
    conversation_id: str | None,
    question: str,
    attachments: list[dict] | None,
    create_conversation_fn: Callable[[str, str], str],
    conversation_belongs_to_fn: Callable[[str, str], bool],
    get_messages_fn: Callable[..., list[dict]],
    add_message_fn: Callable[..., Any],
    max_history_chars: int = DEFAULT_MAX_HISTORY_CHARS,
) -> tuple[str, list[dict], str]:
    """Create or validate a conversation, load trimmed history, and persist the user turn."""
    conv_id = conversation_id
    if not conv_id:
        title = question[:80].strip() or "New conversation"
        conv_id = create_conversation_fn(user_id, title)
    elif not conversation_belongs_to_fn(conv_id, user_id):
        raise ConversationNotFoundError("Conversation not found")

    history_rows = get_messages_fn(conv_id, limit=20)
    history = trim_history(
        [{"role": message["role"], "content": message["content"]} for message in history_rows],
        max_chars=max_history_chars,
    )
    user_message_id = add_message_fn(conv_id, "user", question, attachments=attachments)
    return conv_id, history, user_message_id


def finish_conversation_turn(
    *,
    conv_id: str,
    user_id: str,
    answer: str,
    latency_ms: int,
    add_message_fn: Callable[..., Any],
    log_event_fn: Callable[[str, str, dict], Any],
    usage: dict | None = None,
    model: str | None = None,
) -> str | None:
    """Persist the assistant turn and record request latency. Returns message id."""
    msg_id = add_message_fn(conv_id, "assistant", answer)
    metadata: dict[str, Any] = {"latency_ms": latency_ms}
    if usage:
        from observability import compute_cost

        billed = float(usage.get("billed_input_tokens", usage.get("input_tokens", 0)))
        output = int(usage.get("output_tokens", 0))
        metadata["input_tokens"] = int(usage.get("input_tokens", 0))
        metadata["output_tokens"] = output
        metadata["billed_input_tokens"] = billed
        metadata["estimated_cost_usd"] = compute_cost(model or "unknown", billed, output)
    if model:
        metadata["model"] = model
    log_event_fn("chat_query", user_id, metadata)
    return msg_id


def _maybe_persist_trace(engine, trace_data_dir: Path | None) -> None:
    """Write orchestrator trace to disk if available. Never raises."""
    if trace_data_dir is None:
        return
    try:
        orch = getattr(engine, "_orchestrator", None)
        if orch is None:
            return
        trace = getattr(orch, "_trace", None)
        session_id = getattr(orch, "_session_id", None)
        if not trace or not session_id:
            return
        from advisor.trace_store import purge_old_traces, write_trace

        write_trace(trace_data_dir, session_id, trace)
        purge_old_traces(trace_data_dir)
    except Exception:
        logger.debug("trace_persist_failed", exc_info=True)


def _collect_usage_from_engine(engine) -> dict | None:
    """Extract token usage from the engine after a request. Never raises."""
    try:
        orch = getattr(engine, "_orchestrator", None)
        if orch is not None:
            usage = getattr(orch, "_total_usage", None)
            if usage and (usage.get("input_tokens", 0) or usage.get("output_tokens", 0)):
                return dict(usage)
        llm = getattr(engine, "llm", None)
        if llm is not None:
            return getattr(llm, "_last_usage", None)
    except Exception:
        pass
    return None


def _get_model_name(engine) -> str | None:
    """Extract the model name from the engine. Never raises."""
    try:
        llm = getattr(engine, "llm", None)
        if llm is None:
            return None
        return getattr(llm, "model_name", None) or getattr(llm, "model", None)
    except Exception:
        return None


def run_advice(
    engine,
    question: str,
    *,
    advice_type: str = "general",
    conversation_history: list[dict] | None = None,
    attachment_ids: list[str] | None = None,
    event_callback: Callable[[dict], Any] | None = None,
    trace_data_dir: Path | None = None,
) -> dict[str, Any]:
    """Run an advisor request and return the answer with latency metadata."""
    start = time.monotonic()
    ask_result_method = getattr(type(engine), "ask_result", None)
    if callable(ask_result_method):
        result = engine.ask_result(
            question,
            advice_type=advice_type,
            conversation_history=conversation_history,
            attachment_ids=attachment_ids,
            event_callback=event_callback,
        )
        _maybe_persist_trace(engine, trace_data_dir)
        payload = {
            "answer": result.answer,
            "latency_ms": int((time.monotonic() - start) * 1000),
            "council_used": getattr(result, "council_used", False),
            "council_member_count": getattr(result, "council_member_count", 0),
            "council_providers": getattr(result, "council_providers", []),
            "council_failed_providers": getattr(result, "council_failed_providers", []),
            "council_partial": getattr(result, "council_partial", False),
            "usage": _collect_usage_from_engine(engine),
            "model": _get_model_name(engine),
        }
        return payload

    answer = engine.ask(
        question,
        advice_type=advice_type,
        conversation_history=conversation_history,
        attachment_ids=attachment_ids,
        event_callback=event_callback,
    )
    _maybe_persist_trace(engine, trace_data_dir)
    return {
        "answer": answer,
        "latency_ms": int((time.monotonic() - start) * 1000),
        "council_used": False,
        "council_member_count": 0,
        "council_providers": [],
        "council_failed_providers": [],
        "council_partial": False,
        "usage": _collect_usage_from_engine(engine),
        "model": _get_model_name(engine),
    }
