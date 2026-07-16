---
name: "harness_core.eventbus.register_background_task"
description: "Register a background task so it is not garbage-collected prematurely."
source: "harness_core/eventbus.py"
---

Register a background task so it is not garbage-collected prematurely.

This method exists for backward-compatibility with older test fixtures;
the current publish path does synchronous delivery and no longer needs
explicit task tracking. Callers may still pass coroutines here — they are
scheduled as :class:`asyncio.Task` objects, stored in
:attr:`_running_tasks`, and automatically removed when they complete.

Args:
    coro: A coroutine (or existing Task) to register and run.

Returns:
    The registered :class:`asyncio.Task` so callers can await it directly.

## Signature
```python
register_background_task(self, coro: Any)
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventBus](harness_core_eventbus_EventBus) - Parent class
