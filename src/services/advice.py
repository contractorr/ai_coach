"""Shared advisor/advice orchestration helpers."""

import time
from typing import Any, Callable

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
    create_conversation_fn: Callable[[str, str], str],
    conversation_belongs_to_fn: Callable[[str, str], bool],
    get_messages_fn: Callable[..., list[dict]],
    add_message_fn: Callable[[str, str, str], Any],
    max_history_chars: int = DEFAULT_MAX_HISTORY_CHARS,
) -> tuple[str, list[dict]]:
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
    add_message_fn(conv_id, "user", question)
    return conv_id, history


def finish_conversation_turn(
    *,
    conv_id: str,
    user_id: str,
    answer: str,
    latency_ms: int,
    add_message_fn: Callable[[str, str, str], Any],
    log_event_fn: Callable[[str, str, dict], Any],
) -> None:
    """Persist the assistant turn and record request latency."""
    add_message_fn(conv_id, "assistant", answer)
    log_event_fn("chat_query", user_id, {"latency_ms": latency_ms})


def run_advice(
    engine,
    question: str,
    *,
    advice_type: str = "general",
    conversation_history: list[dict] | None = None,
    event_callback: Callable[[dict], Any] | None = None,
) -> dict[str, Any]:
    """Run an advisor request and return the answer with latency metadata."""
    start = time.monotonic()
    answer = engine.ask(
        question,
        advice_type=advice_type,
        conversation_history=conversation_history,
        event_callback=event_callback,
    )
    return {
        "answer": answer,
        "latency_ms": int((time.monotonic() - start) * 1000),
    }
