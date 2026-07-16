---
name: "harness_core.event_types.ToolErrorPayload"
description: "Event payload for a tool-call error."
source: "harness_core/event_types.py"
---

Event payload for a tool-call error.

Carries everything needed to render a single ``display_error`` invocation
triggered by an ERROR kind output from agent.handle_prompt(). Subscribers
reconstruct the display by forwarding all fields back through
:func:`harness_core.terminal_io.display.display_error`.

Attributes:
    message: The error description text, or None if no message provided.

## Methods
None

## Class Variables
- `message`: str

## References
- [Module: harness_core.event_types](harness_core_event_types) - Parent module
- Base class: `EventPayload`
- `message`: str
