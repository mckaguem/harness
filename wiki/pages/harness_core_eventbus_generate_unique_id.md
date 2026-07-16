---
name: "harness_core.eventbus.generate_unique_id"
description: "Generate a unique identifier with an optional prefix."
source: "harness_core/eventbus.py"
---

Generate a unique identifier with an optional prefix.

Args:
    prefix: Optional prefix to prepend to the UUID (e.g., "TaskList", "Agent")

Returns:
    A unique identifier string in the format "prefix.uuid" or just "uuid"

## Signature
```python
generate_unique_id(prefix: str) -> str
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
