---
name: "harness_core.session.context_compression._must_preserve"
description: "Return True for messages whose content MUST be preserved verbatim."
source: "harness_core/session/context_compression.py"
---

Return True for messages whose content MUST be preserved verbatim.

System messages and tool_calls-carrying messages are preserved as-is so the
agent's behaviour definition and strict tool-call sequencing remain intact.
Tool-result messages are no longer in this list — they are dispatched to
name-specific helpers (``compress_list_dir``, ``compress_file_operation``)
or left alone for unknown tools.

## Signature
```python
_must_preserve(msg: dict) -> bool
```

## References
- [Module: harness_core.session.context_compression](harness_core_session_context_compression) - Parent module
