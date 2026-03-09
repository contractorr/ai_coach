"""Tests for LLM provider generate_with_tools implementations."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from llm.base import GenerateResponse, ToolCall, ToolDefinition, ToolResult
from llm.providers.claude import ClaudeProvider
from llm.providers.openai import OpenAIProvider

SAMPLE_TOOLS = [
    ToolDefinition(
        name="get_weather",
        description="Get weather for a location",
        input_schema={
            "type": "object",
            "properties": {
                "location": {"type": "string"},
            },
            "required": ["location"],
        },
    ),
]


class TestToolDefinitionDataclasses:
    def test_tool_definition(self):
        td = ToolDefinition(name="foo", description="bar", input_schema={"type": "object"})
        assert td.name == "foo"
        assert td.description == "bar"

    def test_tool_call(self):
        tc = ToolCall(id="call_1", name="foo", arguments={"a": 1})
        assert tc.id == "call_1"
        assert tc.arguments == {"a": 1}

    def test_tool_result(self):
        tr = ToolResult(tool_call_id="call_1", content="result")
        assert not tr.is_error

    def test_tool_result_error(self):
        tr = ToolResult(tool_call_id="call_1", content="bad", is_error=True)
        assert tr.is_error

    def test_generate_response_defaults(self):
        r = GenerateResponse(content="hi")
        assert r.finish_reason == "stop"
        assert r.tool_calls == []

    def test_generate_response_with_tools(self):
        tc = ToolCall(id="1", name="foo", arguments={})
        r = GenerateResponse(content=None, tool_calls=[tc], finish_reason="tool_calls")
        assert r.content is None
        assert len(r.tool_calls) == 1


class TestClaudeToolCalling:
    def _make_provider(self):
        mock_client = MagicMock()
        return ClaudeProvider(client=mock_client), mock_client

    def test_text_only_response(self):
        provider, client = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(type="text", text="Hello")]
        mock_resp.stop_reason = "end_turn"
        client.messages.create.return_value = mock_resp

        result = provider.generate_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
            system="Be helpful",
        )

        assert result.content == "Hello"
        assert result.tool_calls == []
        assert result.finish_reason == "stop"

    def test_tool_use_response(self):
        provider, client = self._make_provider()
        tool_block = MagicMock(type="tool_use", id="toolu_1", input={"location": "NYC"})
        tool_block.name = "get_weather"  # .name is special on MagicMock
        mock_resp = MagicMock()
        mock_resp.content = [tool_block]
        mock_resp.stop_reason = "tool_use"
        client.messages.create.return_value = mock_resp

        result = provider.generate_with_tools(
            messages=[{"role": "user", "content": "weather in NYC?"}],
            tools=SAMPLE_TOOLS,
        )

        assert result.finish_reason == "tool_calls"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "get_weather"
        assert result.tool_calls[0].arguments == {"location": "NYC"}
        assert result.tool_calls[0].id == "toolu_1"

    def test_mixed_text_and_tool_response(self):
        provider, client = self._make_provider()
        text_block = MagicMock(type="text", text="Let me check")
        tool_block = MagicMock(
            type="tool_use", id="toolu_2", name="get_weather", input={"location": "LA"}
        )
        mock_resp = MagicMock()
        mock_resp.content = [text_block, tool_block]
        mock_resp.stop_reason = "tool_use"
        client.messages.create.return_value = mock_resp

        result = provider.generate_with_tools(
            messages=[{"role": "user", "content": "weather?"}],
            tools=SAMPLE_TOOLS,
        )

        assert result.content == "Let me check"
        assert len(result.tool_calls) == 1

    def test_max_tokens_finish_reason(self):
        provider, client = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(type="text", text="partial")]
        mock_resp.stop_reason = "max_tokens"
        client.messages.create.return_value = mock_resp

        result = provider.generate_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
        )
        assert result.finish_reason == "max_tokens"

    def test_tool_choice_auto(self):
        provider, client = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(type="text", text="ok")]
        mock_resp.stop_reason = "end_turn"
        client.messages.create.return_value = mock_resp

        provider.generate_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
            tool_choice="auto",
        )

        call_kwargs = client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "auto"}

    def test_tool_choice_required(self):
        provider, client = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(type="text", text="ok")]
        mock_resp.stop_reason = "end_turn"
        client.messages.create.return_value = mock_resp

        provider.generate_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
            tool_choice="required",
        )

        call_kwargs = client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "any"}

    def test_prompt_caching_marks_system_and_first_three_messages(self):
        provider, client = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(type="text", text="ok")]
        mock_resp.stop_reason = "end_turn"
        mock_resp.usage = SimpleNamespace(
            input_tokens=100,
            output_tokens=50,
            cache_creation_input_tokens=80,
            cache_read_input_tokens=20,
        )
        client.messages.create.return_value = mock_resp

        messages = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
            {"role": "user", "content": "third"},
            {"role": "user", "content": "fourth"},
        ]

        result = provider.generate_with_tools(
            messages=messages,
            tools=SAMPLE_TOOLS,
            system="Be helpful",
        )

        call_kwargs = client.messages.create.call_args.kwargs
        assert call_kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
        assert call_kwargs["messages"][0]["content"][0]["cache_control"] == {"type": "ephemeral"}
        assert call_kwargs["messages"][1]["content"][0]["cache_control"] == {"type": "ephemeral"}
        assert call_kwargs["messages"][2]["content"][0]["cache_control"] == {"type": "ephemeral"}
        assert "cache_control" not in call_kwargs["messages"][3]["content"][0]
        assert result.usage["cache_creation_input_tokens"] == 80
        assert result.usage["cache_read_input_tokens"] == 20
        assert result.usage["billed_input_tokens"] == 200.0

    def test_prompt_caching_can_be_disabled(self):
        mock_client = MagicMock()
        provider = ClaudeProvider(client=mock_client, prompt_caching_enabled=False)
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(type="text", text="ok")]
        mock_resp.stop_reason = "end_turn"
        mock_resp.usage = SimpleNamespace(input_tokens=10, output_tokens=5)
        mock_client.messages.create.return_value = mock_resp

        provider.generate_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
            system="Be helpful",
        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "cache_control" not in call_kwargs["system"][0]
        assert "cache_control" not in call_kwargs["messages"][0]["content"][0]

    def test_convert_messages_with_tool_results(self):
        client = MagicMock()
        provider = ClaudeProvider(client=client, prompt_caching_enabled=False)
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(type="text", text="Got it")]
        mock_resp.stop_reason = "end_turn"
        client.messages.create.return_value = mock_resp

        messages = [
            {"role": "user", "content": "weather?"},
            {
                "role": "assistant",
                "tool_calls": [
                    {"id": "toolu_1", "name": "get_weather", "arguments": {"location": "NYC"}}
                ],
            },
            {"role": "tool", "tool_call_id": "toolu_1", "content": '{"temp": 72}'},
        ]

        provider.generate_with_tools(messages=messages, tools=SAMPLE_TOOLS)

        call_kwargs = client.messages.create.call_args.kwargs
        api_msgs = call_kwargs["messages"]

        # user, assistant with tool_use blocks, user with tool_result
        assert api_msgs[0] == {"role": "user", "content": "weather?"}
        assert api_msgs[1]["role"] == "assistant"
        assert api_msgs[1]["content"][0]["type"] == "tool_use"
        assert api_msgs[2]["role"] == "user"
        assert api_msgs[2]["content"][0]["type"] == "tool_result"

    def test_consecutive_tool_results_merged(self):
        """Multiple tool results should be merged into one user message."""
        provider = ClaudeProvider(client=MagicMock())
        messages = [
            {"role": "user", "content": "both?"},
            {
                "role": "assistant",
                "tool_calls": [
                    {"id": "t1", "name": "a", "arguments": {}},
                    {"id": "t2", "name": "b", "arguments": {}},
                ],
            },
            {"role": "tool", "tool_call_id": "t1", "content": "r1"},
            {"role": "tool", "tool_call_id": "t2", "content": "r2"},
        ]

        converted = provider._convert_messages(messages)
        # Should be: user, assistant, user (with 2 tool_results)
        assert len(converted) == 3
        assert len(converted[2]["content"]) == 2

    def test_auth_error_propagated(self):
        from anthropic import AuthenticationError

        provider, client = self._make_provider()
        client.messages.create.side_effect = AuthenticationError(
            message="bad key", response=MagicMock(status_code=401), body={}
        )

        from llm import LLMAuthError

        with pytest.raises(LLMAuthError):
            provider.generate_with_tools(
                messages=[{"role": "user", "content": "hi"}],
                tools=SAMPLE_TOOLS,
            )


class TestOpenAIToolCalling:
    def _make_provider(self):
        mock_client = MagicMock()
        return OpenAIProvider(client=mock_client), mock_client

    def test_text_only_response(self):
        provider, client = self._make_provider()
        msg = MagicMock(content="Hello", tool_calls=None)
        choice = MagicMock(message=msg, finish_reason="stop")
        client.chat.completions.create.return_value = MagicMock(choices=[choice])

        result = provider.generate_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
        )

        assert result.content == "Hello"
        assert result.tool_calls == []
        assert result.finish_reason == "stop"

    def test_tool_call_response(self):
        provider, client = self._make_provider()
        tc = MagicMock()
        tc.id = "call_1"
        tc.function.name = "get_weather"
        tc.function.arguments = '{"location": "NYC"}'
        msg = MagicMock(content=None, tool_calls=[tc])
        choice = MagicMock(message=msg, finish_reason="tool_calls")
        client.chat.completions.create.return_value = MagicMock(choices=[choice])

        result = provider.generate_with_tools(
            messages=[{"role": "user", "content": "weather?"}],
            tools=SAMPLE_TOOLS,
        )

        assert result.finish_reason == "tool_calls"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "get_weather"
        assert result.tool_calls[0].arguments == {"location": "NYC"}

    def test_length_maps_to_max_tokens(self):
        provider, client = self._make_provider()
        msg = MagicMock(content="partial", tool_calls=None)
        choice = MagicMock(message=msg, finish_reason="length")
        client.chat.completions.create.return_value = MagicMock(choices=[choice])

        result = provider.generate_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
        )
        assert result.finish_reason == "max_tokens"

    def test_tool_defs_format(self):
        provider, client = self._make_provider()
        msg = MagicMock(content="ok", tool_calls=None)
        choice = MagicMock(message=msg, finish_reason="stop")
        client.chat.completions.create.return_value = MagicMock(choices=[choice])

        provider.generate_with_tools(
            messages=[{"role": "user", "content": "hi"}],
            tools=SAMPLE_TOOLS,
        )

        call_kwargs = client.chat.completions.create.call_args.kwargs
        tools = call_kwargs["tools"]
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "get_weather"
        assert "parameters" in tools[0]["function"]

    def test_messages_with_tool_results(self):
        provider, client = self._make_provider()
        msg = MagicMock(content="72 degrees", tool_calls=None)
        choice = MagicMock(message=msg, finish_reason="stop")
        client.chat.completions.create.return_value = MagicMock(choices=[choice])

        messages = [
            {"role": "user", "content": "weather?"},
            {
                "role": "assistant",
                "tool_calls": [
                    {"id": "call_1", "name": "get_weather", "arguments": {"location": "NYC"}}
                ],
            },
            {"role": "tool", "tool_call_id": "call_1", "content": '{"temp": 72}'},
        ]

        provider.generate_with_tools(messages=messages, tools=SAMPLE_TOOLS, system="sys")

        call_kwargs = client.chat.completions.create.call_args.kwargs
        api_msgs = call_kwargs["messages"]
        # system + user + assistant + tool
        assert api_msgs[0]["role"] == "system"
        assert api_msgs[1]["role"] == "user"
        assert api_msgs[2]["role"] == "assistant"
        assert "tool_calls" in api_msgs[2]
        assert api_msgs[3]["role"] == "tool"
