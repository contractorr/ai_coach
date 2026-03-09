"""Agentic orchestrator — LLM tool-calling loop."""

from collections.abc import Callable

import structlog

from llm.base import LLMProvider
from services.tool_registry import ToolRegistry

from .context_compressor import ContextCompressor

logger = structlog.get_logger()


class AgenticOrchestrator:
    """Runs an LLM tool-calling loop until the model responds with text."""

    def __init__(
        self,
        llm: LLMProvider,
        registry: ToolRegistry,
        system_prompt: str,
        max_iterations: int = 10,
        cheap_llm: LLMProvider | None = None,
        token_threshold: int = 100_000,
    ):
        self.llm = llm
        self.registry = registry
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.compressor = ContextCompressor(
            cheap_llm=cheap_llm,
            token_threshold=token_threshold,
        )
        self._total_input_tokens = 0

    def run(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
        event_callback: Callable[[dict], None] | None = None,
    ) -> str:
        messages = list(conversation_history or [])
        messages.append({"role": "user", "content": user_message})
        tools = self.registry.get_definitions()

        for iteration in range(self.max_iterations):
            response = self.llm.generate_with_tools(
                messages=messages,
                tools=tools,
                system=self.system_prompt,
            )

            logger.debug(
                "agentic_iteration",
                iteration=iteration,
                finish_reason=response.finish_reason,
                tool_call_count=len(response.tool_calls) if response.tool_calls else 0,
            )
            if response.usage:
                self._total_input_tokens = int(response.usage.get("input_tokens", 0))
            else:
                logger.warning("agentic_usage_missing", iteration=iteration)

            # LLM finished with text - return it
            if response.finish_reason == "stop" or not response.tool_calls:
                logger.info("agentic_complete", iterations=iteration + 1)
                content = response.content or ""
                if event_callback:
                    event_callback({"type": "answer", "content": content})
                return content

            # Build assistant message with tool calls
            assistant_msg = {
                "role": "assistant",
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in response.tool_calls
                ],
            }
            if response.content:
                assistant_msg["content"] = response.content
            messages.append(assistant_msg)

            # Execute each tool call and append results
            for tc in response.tool_calls:
                logger.info("tool_call", tool=tc.name, args=list(tc.arguments.keys()))
                if event_callback:
                    event_callback({"type": "tool_start", "tool": tc.name})

                result_text = self.registry.execute(tc.name, tc.arguments)
                is_error = '"error"' in result_text[:50]

                logger.info(
                    "tool_result",
                    tool=tc.name,
                    chars=len(result_text),
                    is_error=is_error,
                )
                if event_callback:
                    event_callback({"type": "tool_done", "tool": tc.name, "is_error": is_error})

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.name,
                        "content": result_text,
                        "is_error": is_error,
                    }
                )

            messages = self.compressor.compress_if_needed(messages, self._total_input_tokens)

        # Max iterations reached - return whatever we have
        logger.warning("agentic_max_iterations", max=self.max_iterations)
        if response.content:
            return response.content
        return "I wasn't able to complete that request within the allowed steps."
