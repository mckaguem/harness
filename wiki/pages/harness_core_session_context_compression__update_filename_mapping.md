---
name: "harness_core.session.context_compression._update_filename_mapping"
description: "Populate *filename_by_tool_id* from a list of tool_call entries."
source: "harness_core/session/context_compression.py"
---

Populate *filename_by_tool_id* from a list of tool_call entries.

For each entry whose function is in ``file_operating_tools``, extract the
``filename`` argument (preferring the ``filename`` key; falling back to
positional argument 0) and record it keyed by the call id.

## Signature
```python
_update_filename_mapping(tool_calls, file_operating_tools: set[str], filename_by_tool_id: dict[str, str]) -> None
```

## References
- [Module: harness_core.session.context_compression](harness_core_session_context_compression) - Parent module
