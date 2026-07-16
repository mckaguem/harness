---
name: "harness_core.tools.subagent_manager.await_one"
description: "Block until a background job finishes and return its ToolResult."
source: "harness_core/tools/subagent_manager.py"
---

Block until a background job finishes and return its ToolResult.

Args:
    identifier: If given, wait specifically on that job's future. If
        ``None``, block until the *first* currently-running job
        completes and return its result.
    timeout: Optional per-future timeout (seconds). ``None`` = no limit.

Raises:
    RuntimeError: if there are no running subagents to await.
    Exception: re-raises whatever the background job raised (e.g. on a
        timeout) so callers observe the real failure.

## Signature
```python
await_one(self, identifier: str | None, timeout: float | None) -> ToolResult
```

## References
- [Module: harness_core.tools.subagent_manager](harness_core_tools_subagent_manager) - Parent module
- [Class: SubagentManager](harness_core_tools_subagent_manager_SubagentManager) - Parent class
