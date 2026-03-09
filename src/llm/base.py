"""Base LLM provider abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class LLMError(Exception):
    """Base LLM error."""


class LLMRateLimitError(LLMError):
    """Rate limit hit."""


class LLMAuthError(LLMError):
    """Authentication failure."""


@dataclass
class ToolDefinition:
    """Tool definition for LLM tool calling."""

    name: str
    description: str
    input_schema: dict  # JSON Schema


@dataclass
class ToolCall:
    """A tool call requested by the LLM."""

    id: str
    name: str
    arguments: dict


@dataclass
class ToolResult:
    """Result of executing a tool call."""

    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class GenerateResponse:
    """Response from generate_with_tools."""

    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"  # "stop" | "tool_calls" | "max_tokens"
    usage: dict | None = None


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    provider_name: str = "base"

    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 2000,
        use_thinking: bool = False,
    ) -> str:
        """Generate a response from messages.

        Args:
            messages: List of {"role": ..., "content": ...} dicts
            system: Optional system prompt
            max_tokens: Max response tokens
            use_thinking: If True and provider supports it, enable extended thinking

        Returns:
            Generated text
        """
        ...

    @abstractmethod
    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[ToolDefinition],
        system: str | None = None,
        max_tokens: int = 2000,
        tool_choice: str = "auto",
    ) -> GenerateResponse:
        """Generate a response with tool-calling support.

        Args:
            messages: Conversation messages (may include tool results)
            tools: Available tool definitions
            system: Optional system prompt
            max_tokens: Max response tokens
            tool_choice: "auto" or "required"

        Returns:
            GenerateResponse with content and/or tool_calls
        """
        ...
