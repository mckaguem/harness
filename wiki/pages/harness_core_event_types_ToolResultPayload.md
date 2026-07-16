---
name: "harness_core.event_types.ToolResultPayload"
description: "Event payload for a tool result."
source: "harness_core/event_types.py"
---

Event payload for a tool result.

Carries everything needed to render a single ``display_tool_result`` invocation.
Subscribers reconstruct the display by forwarding all fields back through
:func:`harness_core.terminal_io.display.display_tool_result`.

Attributes:
    func_name: Name of the tool that produced the result (used as fallback title).
    result_title: Title override from the ToolResult object, or None.
    result_display_text: The display text content of the ToolResult.
    result_theme: Color/theme string for rendering (e.g. "info", "error").
    result_type_tag: Type tag from the ToolResult, defaults to "text".

## Methods
None

## Class Variables
- `func_name`: str
- `result_title`: str | None
- `result_display_text`: str
- `result_theme`: str
- `result_type_tag`: str

## References
- [Module: harness_core.event_types](harness_core_event_types) - Parent module
- Base class: `EventPayload`
- `func_name`: str
- `result_title`: str | None
- `result_display_text`: str
- `result_theme`: str - info
- `result_type_tag`: str - text
