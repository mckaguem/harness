---
name: "harness_core.eventbus.default_handler"
description: "Default handler for events without a specific handler method."
source: "harness_core/eventbus.py"
---

Default handler for events without a specific handler method.

Override this method in subclasses to provide default handling behavior.

Args:
    event: The event that was not handled by a specific method

## Signature
```python
default_handler(self, event: Event) -> None
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventListener](harness_core_eventbus_EventListener) - Parent class
