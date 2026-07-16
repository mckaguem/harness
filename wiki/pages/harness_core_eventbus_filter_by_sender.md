---
name: "harness_core.eventbus.filter_by_sender"
description: "Decorator that only invokes the wrapped async handler when the event's"
source: "harness_core/eventbus.py"
---

Decorator that only invokes the wrapped async handler when the event's
sender id matches the supplied regular expression.

If the sender does not match, the handler is skipped entirely.

Args:
    sender_regex: Regular expression pattern to match against event.sender

## Signature
```python
filter_by_sender(sender_regex: str)
```

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
