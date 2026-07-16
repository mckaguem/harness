---
name: "harness_core.eventbus.set_event_loop"
description: "Register the application's main running event loop."
source: "harness_core/eventbus.py"
---

Register the application's main running event loop.

When set, methods that publish events off the loop thread (such as the
agent loop running on a worker thread) will marshal delivery onto this
loop via ``call_soon_threadsafe`` so subscribed listeners still fire on
the correct thread. Pass ``None`` to clear the registration.

## Signature
```python
set_event_loop(loop: Optional['asyncio.AbstractEventLoop']) -> None
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
