"""OpenAI-compatible LLM provider for custom endpoints."""

import json

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

# Lazy exception references
_openai_exceptions = None
_httpx_exceptions = None


def _get_openai_exceptions():
    global _openai_exceptions
    if _openai_exceptions is None:
        try:
            from openai import APIError, AuthenticationError, RateLimitError

            _openai_exceptions = (AuthenticationError, RateLimitError, APIError)
        except ImportError:
            _openai_exceptions = ()
    return _openai_exceptions


def _get_httpx_exceptions():
    global _httpx_exceptions
    if _httpx_exceptions is None:
        try:
            import httpx

            _httpx_exceptions = (httpx.TimeoutException, httpx.ConnectError)
        except ImportError:
            _httpx_exceptions = ()
    return _httpx_exceptions


def _handle_error(e: Exception, display_name: str):
    openai_exc = _get_openai_exceptions()
    httpx_exc = _get_httpx_exceptions()

    if openai_exc and len(openai_exc) == 3:
        AuthErr, RateErr, ApiErr = openai_exc
        if isinstance(e, AuthErr):
            raise LLMAuthError(f"{display_name} auth failed: {e}") from e
        if isinstance(e, RateErr):
            raise LLMRateLimitError(f"{display_name} rate limit: {e}") from e
        if isinstance(e, ApiErr):
            raise LLMError(f"{display_name} API error: {e}") from e

    if httpx_exc and len(httpx_exc) == 2:
        TimeoutErr, ConnectErr = httpx_exc
        if isinstance(e, TimeoutErr):
            raise LLMError(f"{display_name} timeout: {e}") from e
        if isinstance(e, ConnectErr):
            raise LLMError(f"{display_name} connection failed: {e}") from e

    raise LLMError(f"{display_name} error: {e}") from e


class OpenAICompatibleProvider(LLMProvider):
    """Generic provider for OpenAI-compatible endpoints."""

    provider_name = "openai_compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        display_name: str | None = None,
    ):
        if not base_url:
            raise LLMError("base_url required for OpenAI-compatible provider")
        if not api_key:
            raise LLMError("api_key required for OpenAI-compatible provider")
        if not model:
            raise LLMError("model required for OpenAI-compatible provider")

        self.base_url = base_url
        self.model = model
        self.model_name = model
        self.display_name = display_name or "OpenAI-compatible"
        self._last_usage: dict | None = None

        try:
            from openai import OpenAI
        except ImportError:
            raise LLMError("openai package required for OpenAI-compatible providers")

        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def _extract_and_record_usage(self, response) -> dict | None:
        usage = getattr(response, "usage", None)
        if not usage:
            return None
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        metrics.token_usage(self.model, input_tokens, output_tokens)
        result = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "billed_input_tokens": float(input_tokens),
        }
        self._last_usage = result
        return result

    def generate(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 2000,
        use_thinking: bool = False,
    ) -> str:
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=full_messages,
            )
            self._extract_and_record_usage(response)
            return self._strip_think_tags(response.choices[0].message.content)
        except Exception as e:
            _handle_error(e, self.display_name)

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[ToolDefinition],
        system: str | None = None,
        max_tokens: int = 2000,
        tool_choice: str = "auto",
    ) -> GenerateResponse:
        # Map ToolDefinitions to OpenAI function format
        tool_defs = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema,
                },
            }
            for t in tools
        ]

        # Build messages with system prompt
        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})

        # Convert generic messages to OpenAI format
        for msg in messages:
            role = msg.get("role")

            if role == "assistant" and msg.get("tool_calls"):
                # Assistant message with tool calls
                oai_tool_calls = []
                for tc in msg["tool_calls"]:
                    oai_tool_calls.append(
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["arguments"]),
                            },
                        }
                    )
                api_messages.append(
                    {
                        "role": "assistant",
                        "content": msg.get("content"),
                        "tool_calls": oai_tool_calls,
                    }
                )

            elif role == "tool":
                api_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg["tool_call_id"],
                        "content": msg["content"],
                    }
                )

            else:
                api_messages.append(msg)

        # Map tool_choice
        tc = tool_choice if tool_choice in ("auto", "required", "none") else "auto"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=api_messages,
                tools=tool_defs,
                tool_choice=tc,
            )

            choice = response.choices[0]
            message = choice.message

            # Parse tool calls
            tool_calls = []
            if message.tool_calls:
                for tc_obj in message.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            id=tc_obj.id,
                            name=tc_obj.function.name,
                            arguments=json.loads(tc_obj.function.arguments),
                        )
                    )

            content = self._strip_think_tags(message.content)

            if choice.finish_reason == "tool_calls":
                finish = "tool_calls"
            elif choice.finish_reason == "length":
                finish = "max_tokens"
            else:
                finish = "stop"

            usage = self._extract_and_record_usage(response)
            return GenerateResponse(
                content=content, tool_calls=tool_calls, finish_reason=finish, usage=usage
            )

        except Exception as e:
            _handle_error(e, self.display_name)
