---
name: "harness_core.session.context_compression.compress_session"
description: "Compress a session's messages and rotate its save file."
source: "harness_core/session/context_compression.py"
---

Compress a session's messages and rotate its save file.

Args:
    session: An object with .messages (list) and .filepath (str) attributes.
    fraction: The proportion of the tail to preserve (passed to compress_messages).

Returns:
    The new filepath string, or None if compression made no changes.

## Signature
```python
compress_session(session: Session, fraction: float) -> str | None
```

## References
- [Module: harness_core.session.context_compression](harness_core_session_context_compression) - Parent module
