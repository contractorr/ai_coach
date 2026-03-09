"""Tests for shared advisor/advice orchestration helpers."""

from unittest.mock import MagicMock

import pytest

from services.advice import (
    ConversationNotFoundError,
    finish_conversation_turn,
    run_advice,
    start_conversation_turn,
    trim_history,
)


def test_trim_history_keeps_recent_messages_within_budget():
    messages = [
        {"role": "user", "content": "a" * 30},
        {"role": "assistant", "content": "b" * 20},
        {"role": "user", "content": "c" * 10},
    ]

    trimmed = trim_history(messages, max_chars=35)

    assert trimmed == messages[1:]


def test_start_conversation_turn_creates_or_validates_and_persists_user_message():
    create_conversation = MagicMock(return_value="conv-1")
    conversation_belongs_to = MagicMock(return_value=True)
    get_messages = MagicMock(return_value=[{"role": "assistant", "content": "Earlier"}])
    add_message = MagicMock()

    conv_id, history = start_conversation_turn(
        user_id="user-1",
        conversation_id=None,
        question="What now?",
        attachments=None,
        create_conversation_fn=create_conversation,
        conversation_belongs_to_fn=conversation_belongs_to,
        get_messages_fn=get_messages,
        add_message_fn=add_message,
    )

    assert conv_id == "conv-1"
    assert history == [{"role": "assistant", "content": "Earlier"}]
    add_message.assert_called_once_with("conv-1", "user", "What now?", attachments=None)


def test_start_conversation_turn_rejects_foreign_conversation():
    with pytest.raises(ConversationNotFoundError):
        start_conversation_turn(
            user_id="user-1",
            conversation_id="conv-x",
            question="What now?",
            attachments=None,
            create_conversation_fn=MagicMock(),
            conversation_belongs_to_fn=MagicMock(return_value=False),
            get_messages_fn=MagicMock(),
            add_message_fn=MagicMock(),
        )


def test_finish_conversation_turn_persists_answer_and_latency():
    add_message = MagicMock()
    log_event = MagicMock()

    finish_conversation_turn(
        conv_id="conv-1",
        user_id="user-1",
        answer="Do this next",
        latency_ms=123,
        add_message_fn=add_message,
        log_event_fn=log_event,
    )

    add_message.assert_called_once_with("conv-1", "assistant", "Do this next")
    log_event.assert_called_once_with("chat_query", "user-1", {"latency_ms": 123})


def test_run_advice_returns_answer_and_latency():
    engine = MagicMock()
    engine.ask.return_value = "Mock advice"

    result = run_advice(
        engine,
        "What should I do?",
        advice_type="general",
        conversation_history=[{"role": "user", "content": "Earlier"}],
    )

    assert result["answer"] == "Mock advice"
    assert result["latency_ms"] >= 0
    engine.ask.assert_called_once()
