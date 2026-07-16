---
name: "harness_core.eventbus.publish"
description: "Broadcasts a message to all subscribed loops safely across threads."
source: "harness_core/eventbus.py"
---

Broadcasts a message to all subscribed loops safely across threads.

When called from a worker thread, schedules delivery onto each target's
event loop via call_soon_threadsafe. When called on the same thread as
the target (e.g., non-TUI mode), delivers directly.

Args:
    event: The event to publish (must have a topic)

## Signature
```python
publish(self, event: Event)
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventBus](harness_core_eventbus_EventBus) - Parent class
