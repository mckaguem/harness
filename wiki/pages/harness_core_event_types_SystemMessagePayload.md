---
name: "harness_core.event_types.SystemMessagePayload"
description: "Event payload for a system-level status/notification message."
source: "harness_core/event_types.py"
---

Event payload for a system-level status/notification message.

Carries a short ``title`` and a longer ``message`` body, suitable for
rendering as a system panel (e.g. an "Agent Ready" banner or an
"Auto-Compression" notice). Mirrors the signature of
:func:`harness_core.terminal_io.display.print_system`.

## Methods
None

## Class Variables
- `title`: str
- `message`: str

## References
- [Module: harness_core.event_types](harness_core_event_types) - Parent module
- Base class: `EventPayload`
- `title`: str
- `message`: str
