---
name: "harness_core.model.provider._to_responses_input"
description: "Convert chat-style ``messages`` into a valid Responses API request."
source: "harness_core/model/provider.py"
---

Convert chat-style ``messages`` into a valid Responses API request.

The OpenAI **Responses** API does not accept the Chat-Completions
message schema verbatim.  In particular it rejects ``role: "tool"`` items
(tool results must be ``function_call_output`` items) and requires assistant
tool calls to be ``function_call`` items.  This helper normalises the
harness's accumulated conversation (which uses the chat schema, including
``role: "tool"`` results and ``tool_calls`` on assistant messages) into
the shape the Responses API expects.

Args:
    messages: List of chat-schema dicts (``role`` + ``content``,
        optionally ``tool_calls`` on assistant and ``tool_call_id`` on tool).

Returns:
    A ``(instructions, input_items)`` tuple where ``instructions`` is the
    concatenated system prompt (or ``None``) and ``input_items`` is the list
    of Responses input items (``message`` / ``function_call`` /
    ``function_call_output``).

## Signature
```python
_to_responses_input(messages: list[Dict]) -> 'tuple[str | None, list[Any]]'
```

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
