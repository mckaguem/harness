---
name: "harness_core.eventbus.Event"
description: "Represents an event in the event bus system."
source: "harness_core/eventbus.py"
---

Represents an event in the event bus system.

Attributes:
    topic: The event topic/name (e.g., 'user_created', 'message_received').
           None for direct messages.
    sender: The identifier of the event sender
    payload: Arbitrary data associated with the event

## Methods
None

## Class Variables
- `topic`: Optional[str]
- `sender`: str
- `payload`: Any

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- `topic`: Optional[str]
- `sender`: str
- `payload`: Any
