---
name: "harness_core.eventbus.publish"
description: "Broadcast to a topic without blocking."
source: "harness_core/eventbus.py"
---

Broadcast to a topic without blocking.

Args:
    topic: The topic to publish to
    payload: Arbitrary data to send

## Signature
```python
publish(self, topic: str, payload: Any) -> None
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventListener](harness_core_eventbus_EventListener) - Parent class
