"""Tests for OpenAIProvider Responses-API request normalisation.

The OpenAI Responses API rejects the Chat-Completions schema verbatim
and returns 400 ("invalid prompt / invalid responses api request").
Two independent conversions were needed:

1. `input` (was `messages`): system -> `instructions`; tool
   results -> `function_call_output`; assistant `tool_calls` ->
   `function_call`; every `message` item's `content` must be a LIST
   of content parts (`[{"type": "input_text", "text": ...}]`).

2. `tools` (was nested under `function` like Chat Completions):
   the Responses API requires a FLATTENED shape with `name`/
   `parameters` at the top level. Sending the nested Chat shape makes
   the server report `name`/`parameters` as "received undefined" ->
   `400 invalid prompt`. THIS was the actual cause of the
   persistent errors (the harness passed Chat tool schemas straight in).

These tests validate the converted payloads against the REAL openai SDK
`ResponseCreateParams` request model (which is exactly what
`client.responses.create(**kwargs)` enforces at request time).
"""
from pydantic import TypeAdapter
from openai.types.responses import ResponseCreateParams
from harness_core.model.provider import (
    _to_responses_input,
    _to_responses_tools,
    OpenAIProvider,
)


def _text(text):
    return [{"type": "input_text", "text": text}]


def _validate(model, **kwargs):
    # Mirrors what client.responses.create does internally.
    TypeAdapter(ResponseCreateParams).validate_python(kwargs)


class TestResponsesInputConversion:
    """Tests for _to_responses_input message normalization."""

    def test_system_message_moves_to_instructions(self):
        instructions, items = _to_responses_input([
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "hi"},
        ])
        assert instructions == "You are helpful."
        assert all(it.get("type") != "system" for it in items)
        assert items[0] == {"type": "message", "role": "user", "content": _text("hi")}

    def test_multiple_system_blocks_concatenated(self):
        instructions, items = _to_responses_input([
            {"role": "system", "content": "A"},
            {"role": "system", "content": "B"},
        ])
        assert instructions == "A\n\nB"
        assert items == []

    def test_tool_result_becomes_function_call_output(self):
        instructions, items = _to_responses_input([
            {"role": "user", "content": "run it"},
            {"role": "tool", "content": "file1.txt", "tool_call_id": "call_1"},
        ])
        assert instructions is None
        assert items == [
            {"type": "message", "role": "user", "content": _text("run it")},
            {
                "type": "function_call_output",
                "call_id": "call_1",
                "output": "file1.txt",
            },
        ]

    def test_assistant_tool_calls_become_function_call_items(self):
        messages = [{
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "call_1",
                "type": "function",
                "function": {"name": "execute_bash", "arguments": '{"command": "ls"}'},
            }],
        }]
        instructions, items = _to_responses_input(messages)
        assert items == [{
            "type": "function_call",
            "call_id": "call_1",
            "name": "execute_bash",
            "arguments": '{"command": "ls"}',
        }]

    def test_assistant_plain_text_uses_content_list(self):
        instructions, items = _to_responses_input([
            {"role": "assistant", "content": "Here are the files."},
        ])
        assert items == [{
            "type": "message",
            "role": "assistant",
            "content": _text("Here are the files."),
        }]

    def test_full_tool_turn_round_trip_is_valid(self):
        messages = [
            {"role": "system", "content": "sys prompt"},
            {"role": "user", "content": "list files"},
            {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call_abc", "type": "function",
                "function": {"name": "execute_bash", "arguments": '{"command": "ls"}'},
            }]},
            {"role": "tool", "content": "a.txt\nb.txt", "tool_call_id": "call_abc"},
            {"role": "assistant", "content": "Here are the files."},
        ]
        instructions, items = _to_responses_input(messages)
        assert instructions == "sys prompt"
        assert all("role" not in it or it["role"] in ("user", "assistant") for it in items)
        assert all(it["type"] in ("message", "function_call", "function_call_output") for it in items)
        for it in items:
            if it["type"] == "message":
                assert isinstance(it["content"], list)
        calls = [i for i in items if i["type"] == "function_call"]
        outputs = [i for i in items if i["type"] == "function_call_output"]
        assert len(calls) == 1 and len(outputs) == 1
        assert calls[0]["call_id"] == outputs[0]["call_id"] == "call_abc"
        assert outputs[0]["output"] == "a.txt\nb.txt"


class TestResponsesTools:
    """Tests for _to_responses_tools flattening + end-to-end requests."""

    def test_to_responses_tools_flattens_chat_schema(self):
        """The real cause of the 400s: Chat tool schemas nest the callable
        under `function`; the Responses API needs it FLATTENED."""
        chat_tools = [{
            "type": "function",
            "function": {
                "name": "execute_bash",
                "description": "Run a shell command.",
                "parameters": {"type": "object", "properties": {"command": {"type": "string"}}},
            },
        }]
        resp_tools = _to_responses_tools(chat_tools)
        assert resp_tools == [{
            "type": "function",
            "name": "execute_bash",
            "description": "Run a shell command.",
            "parameters": {"type": "object", "properties": {"command": {"type": "string"}}},
            "strict": True,
        }]
        # The flattened shape must satisfy the SDK's FunctionToolParam.
        _validate("m", input="hi", tools=resp_tools)

    def test_to_responses_tools_passes_through_flat(self):
        flat = [{"type": "function", "name": "x", "parameters": {"type": "object"}, "strict": True}]
        assert _to_responses_tools(flat) == flat
        assert _to_responses_tools(None) is None

    def test_chat_completion_sends_valid_responses_request(self):
        """End-to-end: chat_completion normalises BOTH messages and tools
        into a payload the SDK accepts (this is what previously 400'd)."""
        client = type("C", (), {})()
        captured = {}

        def create(**kwargs):
            captured.update(kwargs)
            part = type("P", (), {"text": "ok"})()
            msg = type("M", (), {"type": "message", "content": [part]})()
            usage = type("U", (), {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2})()
            return type("R", (), {"output": [msg], "usage": usage})()

        client.responses = type("R", (), {"create": staticmethod(create)})()
        prov = OpenAIProvider(client)
        prov.get_base_url = lambda: "http://localhost:11434"

        messages = [
            {"role": "system", "content": "be nice"},
            {"role": "user", "content": "hi"},
            {"role": "tool", "content": "result", "tool_call_id": "call_x"},
        ]
        chat_tools = [{
            "type": "function",
            "function": {"name": "execute_bash", "parameters": {"type": "object"}},
        }]
        prov.chat_completion(messages, "test-model", tools=chat_tools)

        assert "instructions" in captured
        assert captured["instructions"] == "be nice"
        assert not any(it.get("role") == "tool" for it in captured["input"])
        user_item = next(i for i in captured["input"] if i.get("role") == "user")
        assert isinstance(user_item["content"], list)
        # Tools must be flattened (name at top level, not under `function`).
        assert captured["tools"] == [{
            "type": "function",
            "name": "execute_bash",
            "parameters": {"type": "object"},
            "strict": True,
        }]

