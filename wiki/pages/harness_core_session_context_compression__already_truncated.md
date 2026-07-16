---
name: "harness_core.session.context_compression._already_truncated"
description: "Return True iff ``msg["content"]`` is a string starting with :data:`TRUNCATED_PREFIX`."
source: "harness_core/session/context_compression.py"
---

Return True iff ``msg["content"]`` is a string starting with :data:`TRUNCATED_PREFIX`.

Used to skip messages that were already truncated by an earlier compression pass.

## Signature
```python
_already_truncated(msg: dict) -> bool
```

## References
- [Module: harness_core.session.context_compression](harness_core_session_context_compression) - Parent module
