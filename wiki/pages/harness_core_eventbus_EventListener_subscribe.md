---
name: "harness_core.eventbus.subscribe"
description: "Subscribe this listener to the specified topics and auto-discovered topics."
source: "harness_core/eventbus.py"
---

Subscribe this listener to the specified topics and auto-discovered topics.

This method:
1. Finds all methods on the object named handle_* and extracts topic names
2. Subscribes self to each topic in `topics` list AND discovered topics

Args:
    topics: List of additional topics to subscribe to

## Signature
```python
subscribe(self, topics: List[str]) -> None
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [Class: EventListener](harness_core_eventbus_EventListener) - Parent class
