---
name: "harness_core.eventbus.subscribe"
description: "Bind an agent's existing mailbox to a specific topic."
source: "harness_core/eventbus.py"
---

Bind an agent's existing mailbox to a specific topic.

Args:
    agent_id: Unique identifier for the agent
    topic: The topic to subscribe to

Raises:
    ValueError: If the agent_id is not registered

## Signature
```python
subscribe(self, agent_id: str, topic: str) -> None
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventBus](harness_core_eventbus_EventBus) - Parent class
