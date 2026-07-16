---
name: "harness_core.session.context_compression.compress_messages"
description: "Compress older messages in the list, preserving a portion at the end."
source: "harness_core/session/context_compression.py"
---

Compress older messages in the list, preserving a portion at the end.

Args:
    messages: List of message dictionaries to compress.
    fraction: The proportion (0-1) of messages at the END that should be
              left intact and unmodified. For example, with 100 messages
              and fraction=0.1, the last 10 messages are preserved as-is,
              while the first 90 are compressed by dispatching to
              specialized helpers or halving long content.

Returns:
    A new list where older messages have been truncated (compressed) but
    recent messages remain unchanged. The order is preserved - compressed
    messages come first, followed by preserved messages.

Raises:
    ValueError: If fraction is not between 0 and 1 inclusive.

## Signature
```python
compress_messages(messages: list[dict], fraction: float) -> list[dict]
```

## References
- [Module: harness_core.session.context_compression](harness_core_session_context_compression) - Parent module
