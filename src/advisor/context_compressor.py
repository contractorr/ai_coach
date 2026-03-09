"""Token-aware context compression for the agentic advisor loop."""

from __future__ import annotations

from copy import deepcopy

import structlog

from llm.base import LLMProvider

logger = structlog.get_logger()


class ContextCompressor:
    """Compress older conversation turns while preserving tool-call integrity."""

    def __init__(
        self,
        cheap_llm: LLMProvider | None = None,
        token_threshold: int = 100_000,
        protect_first_n: int = 2,
        protect_last_n: int = 3,
        summary_target_chars: int = 2000,
    ) -> None:
        self.cheap_llm = cheap_llm
        self.token_threshold = token_threshold
        self.protect_first_n = protect_first_n
        self.protect_last_n = protect_last_n
        self.summary_target_chars = summary_target_chars

    def compress_if_needed(self, messages: list[dict], current_input_tokens: int) -> list[dict]:
        """Return a compressed message list when the token budget is exceeded."""
        if current_input_tokens < self.token_threshold:
            return messages
        if len(messages) <= self.protect_first_n + self.protect_last_n:
            return messages

        first = list(messages[: self.protect_first_n])
        last = list(messages[-self.protect_last_n :]) if self.protect_last_n else []
        middle_start = self.protect_first_n
        middle_end = len(messages) - self.protect_last_n if self.protect_last_n else len(messages)
        middle = messages[middle_start:middle_end]
        if not middle:
            return messages

        raw_boundary = middle_start + max(1, len(middle) // 2)
        boundary = self._align_eviction_boundary(messages, raw_boundary)
        if boundary <= middle_start:
            return messages

        evicted = deepcopy(messages[middle_start:boundary])
        if not evicted:
            return messages

        summary_text = self._generate_summary(evicted)
        if not summary_text:
            tool_names = sorted(
                {
                    tool_call.get("name", "unknown")
                    for message in evicted
                    if message.get("role") == "assistant"
                    for tool_call in message.get("tool_calls", [])
                }
            )
            suffix = f" Key tools called: {', '.join(tool_names)}." if tool_names else ""
            summary_text = (
                f"[Earlier context omitted - {len(evicted)} turns summarized.{suffix}]"
            )

        summary_message = {"role": "user", "content": summary_text[: self.summary_target_chars]}
        compressed = first + [summary_message] + deepcopy(messages[boundary:middle_end]) + last
        return self._sanitize_orphans(compressed)

    def _align_eviction_boundary(self, messages: list[dict], raw_boundary: int) -> int:
        """Move the boundary forward so tool calls are evicted with their tool results."""
        boundary = max(0, min(raw_boundary, len(messages)))
        open_tool_call_ids: set[str] = set()

        for message in messages[:boundary]:
            if message.get("role") == "assistant" and message.get("tool_calls"):
                open_tool_call_ids.update(
                    tool_call.get("id")
                    for tool_call in message.get("tool_calls", [])
                    if tool_call.get("id")
                )
            elif message.get("role") == "tool":
                tool_call_id = message.get("tool_call_id")
                if tool_call_id in open_tool_call_ids:
                    open_tool_call_ids.discard(tool_call_id)

        while boundary < len(messages):
            message = messages[boundary]
            if message.get("role") != "tool":
                break
            tool_call_id = message.get("tool_call_id")
            if tool_call_id in open_tool_call_ids:
                open_tool_call_ids.discard(tool_call_id)
                boundary += 1
                continue
            break

        return boundary

    def _generate_summary(self, evicted: list[dict]) -> str | None:
        """Summarize evicted turns via the cheap model, if available."""
        if not self.cheap_llm:
            return None

        rendered = []
        for message in evicted:
            role = message.get("role", "unknown")
            if role == "assistant" and message.get("tool_calls"):
                tool_names = ", ".join(
                    tool_call.get("name", "unknown") for tool_call in message.get("tool_calls", [])
                )
                content = (message.get("content") or "").strip()
                rendered.append(f"[assistant tool_calls={tool_names}] {content[:1000]}")
            else:
                content = str(message.get("content", ""))[:1000]
                rendered.append(f"[{role}] {content}")

        prompt = (
            "Summarize this conversation segment concisely, preserving key facts, tool results, and "
            "decisions.\n\n"
            + "\n".join(rendered)
        )
        try:
            summary = self.cheap_llm.generate(
                messages=[{"role": "user", "content": prompt}],
                system="You are a conversation summarizer. Be concise.",
                max_tokens=800,
            )
            return summary[: self.summary_target_chars]
        except Exception:
            logger.warning("context_compression_summary_failed", exc_info=True)
            return None

    def _sanitize_orphans(self, messages: list[dict]) -> list[dict]:
        """Ensure tool-call and tool-result messages remain well-formed after compression."""
        sanitized: list[dict] = []
        index = 0

        while index < len(messages):
            message = deepcopy(messages[index])

            if message.get("role") == "assistant" and message.get("tool_calls"):
                sanitized.append(message)
                call_ids = [
                    tool_call.get("id")
                    for tool_call in message.get("tool_calls", [])
                    if tool_call.get("id")
                ]
                found_ids: set[str] = set()
                next_index = index + 1
                while next_index < len(messages):
                    next_message = messages[next_index]
                    if next_message.get("role") != "tool":
                        break
                    tool_call_id = next_message.get("tool_call_id")
                    if tool_call_id not in call_ids:
                        break
                    sanitized.append(deepcopy(next_message))
                    if tool_call_id:
                        found_ids.add(tool_call_id)
                    next_index += 1
                for missing_id in call_ids:
                    if missing_id not in found_ids:
                        sanitized.append(self._make_tool_stub(missing_id))
                index = next_index
                continue

            if message.get("role") == "tool":
                sanitized.append(self._make_assistant_stub(message.get("tool_call_id")))
                sanitized.append(message)
                index += 1
                continue

            sanitized.append(message)
            index += 1

        return sanitized

    @staticmethod
    def _make_assistant_stub(tool_call_id: str | None) -> dict:
        safe_id = tool_call_id or "unknown"
        return {
            "role": "assistant",
            "tool_calls": [{"id": safe_id, "name": "unknown", "arguments": {}}],
            "content": "[tool invocation omitted during context compression]",
        }

    @staticmethod
    def _make_tool_stub(tool_call_id: str) -> dict:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": "unknown",
            "content": '{"note": "result omitted during context compression"}',
        }
