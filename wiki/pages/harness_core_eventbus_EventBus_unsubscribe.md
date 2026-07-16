---
name: "harness_core.eventbus.unsubscribe"
description: "Unsubscribe an agent from a specific topic."
source: "harness_core/eventbus.py"
---

Unsubscribe an agent from a specific topic.

Args:
    agent_id: Unique identifier for the agent
    topic: The topic to unsubscribe from

## Signature
```python
unsubscribe(self, agent_id: str, topic: str) -> None
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventBus](harness_core_eventbus_EventBus) - Parent class
