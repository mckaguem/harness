---
name: "harness_core.event_types.ToolCallPayload"
description: "Event payload for an in-progress tool call."
source: "harness_core/event_types.py"
---

Event payload for an in-progress tool call.

Carries everything needed to render a single ``display_tool_call`` invocation.
Subscribers reconstruct the display by forwarding all fields back through
:func:`harness_core.terminal_io.display.display_tool_call`.

Attributes:
    func_name: Name of the tool being called (e.g. "read_file").
    args_str: JSON-encoded arguments string passed to the tool.
    summary: Optional panel title override; if None, display falls back
        to ``"Tool: <func_name>"``.
    pre_content: Agent text said *before* the tool call, rendered in an
        "Agent" panel above the tool-call panel. Defaults to empty string.
    reasoning: Chain-of-thought / reasoning to prepend (above a "---")
        before ``pre_content``. Optional.

## Methods
None

## Class Variables
- `func_name`: str
- `args_str`: str
- `summary`: str | None
- `pre_content`: str
- `reasoning`: str | None

## References
- [Module: harness_core.event_types](harness_core_event_types) - Parent module
- Base class: `EventPayload`
- `func_name`: str
- `args_str`: str
- `summary`: str | None
- `pre_content`: str
- `reasoning`: str | None
