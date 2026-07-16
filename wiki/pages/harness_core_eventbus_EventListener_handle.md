---
name: "harness_core.eventbus.handle"
description: "Dispatch event to the appropriate handler method."
source: "harness_core/eventbus.py"
---

Dispatch event to the appropriate handler method.

Converts the topic to a valid method name (replacing . and - with _)
and calls handle_<topic> if it exists, otherwise calls default_handler.

Args:
    event: The event to handle

## Signature
```python
handle(self, event: Event) -> None
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventListener](harness_core_eventbus_EventListener) - Parent class
