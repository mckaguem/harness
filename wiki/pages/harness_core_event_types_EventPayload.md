---
name: "harness_core.event_types.EventPayload"
description: "Base class for all event payloads."
source: "harness_core/event_types.py"
---

Base class for all event payloads.

This class provides a common base for typed event payloads that can be
passed through the event bus. Subclasses should define their own fields
to represent the specific data for each event type.

Using `kw_only=True` allows subclasses to define required fields without
default values while still having optional fields with defaults in the base.

Example:
    @dataclass(kw_only=True)
    class MyEventPayload(EventPayload):
        message: str
        count: int = 0

## Methods
- **to_dict(self) -> dict[str, Any]** - Convert the payload to a dictionary for serialization

## Class Variables
- `metadata`: dict[str, Any]

## References
- [Module: harness_core.event_types](harness_core_event_types) - Parent module
- [to_dict](harness_core_event_types_EventPayload_to_dict) - Convert the payload to a dictionary for serialization
- `metadata`: dict[str, Any]
