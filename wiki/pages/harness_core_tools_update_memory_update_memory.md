---
name: "harness_core.tools.update_memory.update_memory"
description: "Update the persistent project memory file (MEMORY.md)."
source: "harness_core/tools/update_memory.py"
---

Update the persistent project memory file (MEMORY.md).

The memory file lives at the project root and its contents are auto-injected
into every agent's system prompt, surviving context compression and reloads.

Use mode ``"replace"`` to overwrite the file (or create it) and ``"append"``
to add a new section. After a successful write, the new content will appear in
the system prompt on subsequent sessions.

Args:
    content: The text to write. For mode ``"append"`` a blank-line separator
        is added before the new content.
    mode: ``"replace"`` (default) to overwrite MEMORY.md, or ``"append"`` to
        add to it.

Returns:
    A :class:`~harness_core.tools.tool_result.ToolResult` describing the outcome.

## Signature
```python
update_memory(content: str, mode: str) -> ToolResult
```

## References
- [Module: harness_core.tools.update_memory](harness_core_tools_update_memory) - Parent module
