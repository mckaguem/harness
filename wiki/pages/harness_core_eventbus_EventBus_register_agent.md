---
name: "harness_core.eventbus.register_agent"
description: "Registers an agent using the event loop of the CALLING thread."
source: "harness_core/eventbus.py"
---

Registers an agent using the event loop of the CALLING thread.

If no event loop is currently running (e.g. when called from a
synchronous context such as unit tests), stores ``None`` as the bound
loop — calls to :meth:`publish` will then deliver directly via
:meth:`asyncio.Queue.put_nowait` on the same thread, which is always
safe for synchronous callers.

Args:
    agent_id: Unique identifier for the agent

Returns:
    The ``asyncio.Queue`` mailbox bound to this thread's loop.

Raises:
    ValueError: If the agent_id is already registered

## Signature
```python
register_agent(self, agent_id: str) -> asyncio.Queue[Any]
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventBus](harness_core_eventbus_EventBus) - Parent class
