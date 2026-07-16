---
name: "harness_core.eventbus.send_direct"
description: "Deliver a message directly to a specific agent's mailbox."
source: "harness_core/eventbus.py"
---

Deliver a message directly to a specific agent's mailbox.

This is a point-to-point message (topic is None).

Args:
    sender: Identifier of the sender
    target_agent_id: Unique identifier of the target agent
    payload: Arbitrary data to send

## Signature
```python
send_direct(self, sender: str, target_agent_id: str, payload: Any) -> None
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventBus](harness_core_eventbus_EventBus) - Parent class
