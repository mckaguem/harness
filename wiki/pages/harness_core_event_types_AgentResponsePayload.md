---
name: "harness_core.event_types.AgentResponsePayload"
description: "Event payload for an agent turn response (the LLM's text reply)."
source: "harness_core/event_types.py"
---

Event payload for an agent turn response (the LLM's text reply).

Carries everything needed to render a single ``display_agent_response`` call.
Subscribers reconstruct the display by forwarding all fields back through
:func:`harness_core.terminal_io.display.display_agent_response`.

Attributes:
    content: The raw agent response text (may be empty string).
    response: Additional metadata dict from the provider (e.g. token usage),
        or ``None`` when absent.
    context_length: Length of the model's context window used for the call.
    reasoning: Chain-of-thought / reasoning text, or ``None`` if not present.

## Methods
None

## Class Variables
- `content`: str
- `response`: dict | None
- `context_length`: int
- `reasoning`: str | None

## References
- [Module: harness_core.event_types](harness_core_event_types) - Parent module
- Base class: `EventPayload`
- `content`: str
- `response`: dict | None
- `context_length`: int
- `reasoning`: str | None
