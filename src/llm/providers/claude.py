"""Claude (Anthropic) LLM provider."""

import structlog

from observability import metrics

from ..base import (
    GenerateResponse,
    LLMAuthError,
    LLMError,
    LLMProvider,
    LLMRateLimitError,
    ToolCall,
    ToolDefinition,
)

logger = structlog.get_logger()


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider."""

    provider_name = "claude"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client=None,
        extended_thinking: bool = False,
        prompt_caching_enabled: bool = True,
    ):
        self.model = model or "claude-sonnet-4-6"
        self.model_name = self.model
        self.extended_thinking = extended_thinking
        self.prompt_caching_enabled = prompt_caching_enabled

        if client:
            self.client = client
            return

        try:
            from anthropic import Anthropic
        except ImportError:
            raise LLMError("anthropic package not installed. Run: pip install anthropic")

        self.client = Anthropic(api_key=api_key)

    def _get_exceptions(self):
        from anthropic import APIError, AuthenticationError, RateLimitError

        return AuthenticationError, RateLimitError, APIError

    def _handle_error(self, e: Exception):
        AuthenticationError, RateLimitError, APIError = self._get_exceptions()
        if isinstance(e, AuthenticationError):
            raise LLMAuthError(f"Claude auth failed: {e}") from e
        if isinstance(e, RateLimitError):
            raise LLMRateLimitError(f"Claude rate limit: {e}") from e
        if isinstance(e, APIError):
            raise LLMError(f"Claude API error: {e}") from e
        raise LLMError(f"Claude error: {e}") from e

    def generate(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 2000,
        use_thinking: bool = False,
    ) -> str:
        try:
            self._get_exceptions()
        except ImportError:
            raise LLMError("anthropic package not installed")

        try:
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system

            if use_thinking and self.extended_thinking:
                budget = 8000
                # max_tokens must be strictly greater than budget_tokens
                if kwargs["max_tokens"] <= budget:
                    kwargs["max_tokens"] = budget + 1024
                kwargs["thinking"] = {"type": "enabled", "budget_tokens": budget}

            response = self.client.messages.create(**kwargs)
            self._record_usage(response)

            # With thinking enabled, extract the text block (skip thinking blocks)
            for block in response.content:
                if hasattr(block, "type") and block.type == "text":
                    return block.text
            return response.content[0].text
        except Exception as e:
            self._handle_error(e)

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[ToolDefinition],
        system: str | None = None,
        max_tokens: int = 2000,
        tool_choice: str = "auto",
    ) -> GenerateResponse:
        try:
            self._get_exceptions()
        except ImportError:
            raise LLMError("anthropic package not installed")

        try:
            # Map ToolDefinitions to Anthropic format (already matches)
            tool_defs = [
                {"name": t.name, "description": t.description, "input_schema": t.input_schema}
                for t in tools
            ]

            # Map tool_choice
            if tool_choice == "required":
                tc = {"type": "any"}
            else:
                tc = {"type": "auto"}

            # Convert messages — handle tool results for Anthropic format
            api_messages = self._convert_messages(messages)
            if self.prompt_caching_enabled:
                api_messages = self._apply_prompt_caching(api_messages)

            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": api_messages,
                "tools": tool_defs,
                "tool_choice": tc,
            }
            if system:
                kwargs["system"] = self._build_system_blocks(system)

            response = self.client.messages.create(**kwargs)
            usage = self._record_usage(response)

            # Parse response blocks
            text_parts = []
            tool_calls = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(
                        ToolCall(
                            id=block.id,
                            name=block.name,
                            arguments=block.input,
                        )
                    )

            content = "\n".join(text_parts) if text_parts else None

            if response.stop_reason == "tool_use":
                finish = "tool_calls"
            elif response.stop_reason == "max_tokens":
                finish = "max_tokens"
            else:
                finish = "stop"

            return GenerateResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=finish,
                usage=usage,
            )

        except Exception as e:
            self._handle_error(e)

    def _build_system_blocks(self, system: str) -> list[dict]:
        block = {"type": "text", "text": system}
        if self.prompt_caching_enabled:
            block["cache_control"] = {"type": "ephemeral"}
        return [block]

    def _apply_prompt_caching(self, messages: list[dict]) -> list[dict]:
        cached_messages = []
        cache_breakpoints = 0

        for message in messages:
            if cache_breakpoints >= 3 or message.get("role") not in {"user", "assistant"}:
                cached_messages.append(message)
                continue

            content = message.get("content")
            updated = dict(message)

            if isinstance(content, str):
                updated["content"] = [
                    {
                        "type": "text",
                        "text": content,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
                cache_breakpoints += 1
                cached_messages.append(updated)
                continue

            if isinstance(content, list) and content:
                updated_content = [dict(block) for block in content]
                for index in range(len(updated_content) - 1, -1, -1):
                    if updated_content[index].get("type") == "text":
                        updated_content[index]["cache_control"] = {"type": "ephemeral"}
                        updated["content"] = updated_content
                        cache_breakpoints += 1
                        break
                cached_messages.append(updated)
                continue

            cached_messages.append(message)

        return cached_messages

    @staticmethod
    def _extract_usage(response) -> dict | None:
        usage = getattr(response, "usage", None)
        if not usage:
            return None

        return {
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
            "cache_creation_input_tokens": int(
                getattr(usage, "cache_creation_input_tokens", 0) or 0
            ),
            "cache_read_input_tokens": int(getattr(usage, "cache_read_input_tokens", 0) or 0),
        }

    def _record_usage(self, response) -> dict | None:
        usage = self._extract_usage(response)
        if not usage:
            return None

        billed_input_tokens = usage["input_tokens"] + (usage["cache_creation_input_tokens"] * 1.25)
        logger.debug(
            "anthropic_usage",
            model=self.model,
            input_tokens=usage["input_tokens"],
            cache_write=usage["cache_creation_input_tokens"],
            cache_read=usage["cache_read_input_tokens"],
            output_tokens=usage["output_tokens"],
        )
        metrics.token_usage(
            self.model,
            usage["input_tokens"],
            usage["output_tokens"],
            cache_creation_input_tokens=usage["cache_creation_input_tokens"],
            cache_read_input_tokens=usage["cache_read_input_tokens"],
            billed_input_tokens=billed_input_tokens,
        )
        usage["billed_input_tokens"] = billed_input_tokens
        return usage

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Convert generic messages to Anthropic format.

        Handles tool_calls and tool_result messages:
        - {"role": "assistant", "tool_calls": [...]} → assistant with tool_use content blocks
        - {"role": "tool", "tool_call_id": ..., "content": ...} → user with tool_result content block
        """
        api_messages = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            role = msg.get("role")

            if role == "assistant" and msg.get("tool_calls"):
                # Build content blocks: optional text + tool_use blocks
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    content.append(
                        {
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["name"],
                            "input": tc["arguments"],
                        }
                    )
                api_messages.append({"role": "assistant", "content": content})

            elif role == "tool":
                # Collect consecutive tool results into one user message
                tool_results = []
                while i < len(messages) and messages[i].get("role") == "tool":
                    tr = messages[i]
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tr["tool_call_id"],
                            "content": tr["content"],
                            **({"is_error": True} if tr.get("is_error") else {}),
                        }
                    )
                    i += 1
                api_messages.append({"role": "user", "content": tool_results})
                continue  # skip i += 1 at bottom

            else:
                api_messages.append(msg)

            i += 1

        return api_messages
