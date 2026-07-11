"""Tests for OpenAIProvider Responses-API input normalisation.

The OpenAI **Responses** API rejects the Chat-Completions message schema
verbatim. In particular it returns 400 ("invalid prompt / invalid
responses api request") when the `input` array contains:
  * ``role: "tool"`` items (tool results) — these must be
    ``function_call_output`` items, and
  * assistant messages with ``tool_calls`` — these must be
    ``function_call`` items.
System messages also must NOT be in `input`; they belong in the
top-level `instructions` field.

These tests cover the ``_to_responses_input`` converter and the wiring
into ``chat_completion`` / ``chat_completion_async``.
"""
from harness_core.model.provider import _to_responses_input, OpenAIProvider


def test_system_message_moves_to_instructions():
    instructions, items = _to_responses_input([
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "hi"},
    ])
    assert instructions == "You are helpful."
    # No system item remains in `input`.
    assert all(it.get("type") != "system" for it in items)
    assert items[0] == {"type": "message", "role": "user", "content": "hi"}


def test_multiple_system_blocks_concatenated():
    instructions, items = _to_responses_input([
        {"role": "system", "content": "A"},
        {"role": "system", "content": "B"},
    ])
    assert instructions == "A\n\nB"
    assert items == []


def test_tool_result_becomes_function_call_output():
    instructions, items = _to_responses_input([
        {"role": "user", "content": "run it"},
        {"role": "tool", "content": "file1.txt", "tool_call_id": "call_1"},
    ])
    assert instructions is None
    # The tool result must be a function_call_output referencing call_id,
    # and the preceding user message is preserved as a `message` item.
    assert items == [
        {"type": "message", "role": "user", "content": "run it"},
        {
            "type": "function_call_output",
            "call_id": "call_1",
            "output": "file1.txt",
        },
    ]


def test_assistant_tool_calls_become_function_call_items():
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


def test_full_tool_turn_round_trip_is_valid():
    """A user -> assistant(tool_call) -> tool_result history converts to a
    valid Responses `input` (no role:'tool', tool_calls removed)."""
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
    # Every item uses the Responses `type` discriminator, never role:'tool'.
    assert all("role" not in it or it["role"] in ("user", "assistant") for it in items)
    assert all(it["type"] in ("message", "function_call", "function_call_output") for it in items)

    # The tool call + its result are paired by call_id.
    calls = [i for i in items if i["type"] == "function_call"]
    outputs = [i for i in items if i["type"] == "function_call_output"]
    assert len(calls) == 1 and len(outputs) == 1
    assert calls[0]["call_id"] == outputs[0]["call_id"] == "call_abc"
    assert outputs[0]["output"] == "a.txt\nb.txt"


def test_chat_completion_sends_valid_responses_input():
    """chat_completion must NOT pass raw chat messages to input -- it must
    normalise them (this is what previously caused 400s)."""
    client = type("C", (), {})()
    captured = {}

    def create(**kwargs):
        captured.update(kwargs)
        # Fake a minimal valid Responses response.
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
    prov.chat_completion(messages, "test-model", tools=None)

    assert "instructions" in captured
    assert captured["instructions"] == "be nice"
    # The role:'tool' item must have been converted.
    assert all(it.get("type") == "function_call_output" for it in captured["input"]
               if it.get("type") == "function_call_output")
    assert not any(it.get("role") == "tool" for it in captured["input"])
