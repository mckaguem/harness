---
name: "harness_core.event_types.SessionErrorPayload"
description: "Event payload for an error reported at session level (e.g. auto-compression)."
source: "harness_core/event_types.py"
---

Event payload for an error reported at session level (e.g. auto-compression).

Carries a ``title`` and a longer ``message`` body. Mirrors the signature of
:func:`harness_core.terminal_io.display.print_system` so that subscribers
can render it through the existing ``display_error`` helper.

Attributes:
    title: Short error title (e.g. "Auto-Compression Error"). Defaults to
        "Auto-Compression Error".
    message: Human-readable description of the session-level failure.

## Methods
None

## Class Variables
- `title`: str
- `message`: str

## References
- [Module: harness_core.event_types](harness_core_event_types) - Parent module
- Base class: `EventPayload`
- `title`: str - Auto-Compression Error
- `message`: str
