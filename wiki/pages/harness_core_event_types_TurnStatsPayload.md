---
name: "harness_core.event_types.TurnStatsPayload"
description: "Event payload for post-turn usage + elapsed-time stats pushed to the sidebar."
source: "harness_core/event_types.py"
---

Event payload for post-turn usage + elapsed-time stats pushed to the sidebar.

Carries everything needed to render a single ``display_turn_stats`` call.
Subscribers reconstruct the display by forwarding all fields back through
:func:`harness_core.terminal_io.display.display_turn_stats`.

Attributes:
    response: The raw LLM response dict (usage, eval counts, etc.), or None when absent.
    context_length: Length of the model's context window used for the call.
    elapsed_seconds: Wall-clock time spent on the turn in seconds, or None if not tracked.

## Methods
None

## Class Variables
- `response`: dict | None
- `context_length`: int
- `elapsed_seconds`: float | None

## References
- [Module: harness_core.event_types](harness_core_event_types) - Parent module
- Base class: `EventPayload`
- `response`: dict | None
- `context_length`: int
- `elapsed_seconds`: float | None
