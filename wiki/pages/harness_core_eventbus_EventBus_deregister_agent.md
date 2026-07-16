---
name: "harness_core.eventbus.deregister_agent"
description: "Clean up an agent's mailbox and all of their topic subscriptions."
source: "harness_core/eventbus.py"
---

Clean up an agent's mailbox and all of their topic subscriptions.

Args:
    agent_id: Unique identifier for the agent to deregister

## Signature
```python
deregister_agent(self, agent_id: str) -> None
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventBus](harness_core_eventbus_EventBus) - Parent class
