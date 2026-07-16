---
name: "harness_core.eventbus.send_direct"
description: "Send a message straight to another agent without blocking."
source: "harness_core/eventbus.py"
---

Send a message straight to another agent without blocking.

Args:
    target: The target agent_id
    payload: Arbitrary data to send

## Signature
```python
send_direct(self, target: str, payload: Any) -> None
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventListener](harness_core_eventbus_EventListener) - Parent class
