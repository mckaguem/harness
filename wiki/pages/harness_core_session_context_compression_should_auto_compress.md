---
name: "harness_core.session.context_compression.should_auto_compress"
description: "Determine if auto-compression should be triggered based on context utilization."
source: "harness_core/session/context_compression.py"
---

Determine if auto-compression should be triggered based on context utilization.

Args:
    context_utilization: The current fraction of context used (0-1).
    threshold: The upper limit above which compression should trigger.
              Defaults to 0.5 (50%).

Returns:
    True if the context utilization exceeds the threshold, False otherwise.

Raises:
    ValueError: If context_utilization is not between 0 and 1 inclusive.

## Signature
```python
should_auto_compress(context_utilization: float, threshold: float) -> bool
```

## References
- [Module: harness_core.session.context_compression](harness_core_session_context_compression) - Parent module
