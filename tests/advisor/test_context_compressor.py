"""Tests for token-aware context compression."""

from unittest.mock import MagicMock

from advisor.context_compressor import ContextCompressor


def test_no_compression_needed_returns_messages_unchanged():
    messages = [{"role": "user", "content": "hi"}]
    compressor = ContextCompressor(token_threshold=100)

    assert compressor.compress_if_needed(messages, current_input_tokens=50) == messages


def test_boundary_alignment_evicts_tool_call_and_result_together():
    messages = [
        {"role": "user", "content": "keep"},
        {
            "role": "assistant",
            "tool_calls": [{"id": "call_1", "name": "lookup", "arguments": {}}],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": '{"ok": true}'},
        {"role": "user", "content": "recent"},
    ]
    compressor = ContextCompressor(
        token_threshold=1,
        protect_first_n=1,
        protect_last_n=1,
    )

    compressed = compressor.compress_if_needed(messages, current_input_tokens=10)

    assert compressed[0]["content"] == "keep"
    assert compressed[-1]["content"] == "recent"
    assert all(message.get("role") != "tool" for message in compressed[1:-1])
    assert "Earlier context omitted" in compressed[1]["content"]


def test_orphan_tool_result_gets_stub_assistant():
    compressor = ContextCompressor(token_threshold=1)
    messages = [{"role": "tool", "tool_call_id": "missing", "content": '{"ok": true}'}]

    sanitized = compressor._sanitize_orphans(messages)

    assert sanitized[0]["role"] == "assistant"
    assert sanitized[0]["tool_calls"][0]["id"] == "missing"
    assert sanitized[1]["role"] == "tool"


def test_missing_tool_result_gets_stub_tool_message():
    compressor = ContextCompressor(token_threshold=1)
    messages = [
        {
            "role": "assistant",
            "tool_calls": [{"id": "call_1", "name": "lookup", "arguments": {}}],
        }
    ]

    sanitized = compressor._sanitize_orphans(messages)

    assert sanitized[0]["role"] == "assistant"
    assert sanitized[1]["role"] == "tool"
    assert sanitized[1]["tool_call_id"] == "call_1"


def test_summary_failure_falls_back_to_marker():
    cheap_llm = MagicMock()
    cheap_llm.generate.side_effect = RuntimeError("fail")
    compressor = ContextCompressor(
        cheap_llm=cheap_llm,
        token_threshold=1,
        protect_first_n=1,
        protect_last_n=1,
    )
    messages = [
        {"role": "user", "content": "keep"},
        {"role": "assistant", "content": "old 1"},
        {"role": "user", "content": "old 2"},
        {"role": "assistant", "content": "recent"},
    ]

    compressed = compressor.compress_if_needed(messages, current_input_tokens=10)

    assert "Earlier context omitted" in compressed[1]["content"]


def test_summary_success_uses_cheap_llm_text():
    cheap_llm = MagicMock()
    cheap_llm.generate.return_value = "summary text"
    compressor = ContextCompressor(
        cheap_llm=cheap_llm,
        token_threshold=1,
        protect_first_n=1,
        protect_last_n=1,
    )
    messages = [
        {"role": "user", "content": "keep"},
        {"role": "assistant", "content": "old 1"},
        {"role": "user", "content": "old 2"},
        {"role": "assistant", "content": "recent"},
    ]

    compressed = compressor.compress_if_needed(messages, current_input_tokens=10)

    assert compressed[1]["content"] == "summary text"
