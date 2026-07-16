---
name: "harness_core.eventbus.publish_to_topic"
description: "Broadcast a message to the mailboxes of all subscribed agents."
source: "harness_core/eventbus.py"
---

Broadcast a message to the mailboxes of all subscribed agents.

Args:
    sender: Identifier of the sender
    topic: The topic to publish to
    payload: Arbitrary data to send

## Signature
```python
publish_to_topic(self, sender: str, topic: str, payload: Any) -> None
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventBus](harness_core_eventbus_EventBus) - Parent class
