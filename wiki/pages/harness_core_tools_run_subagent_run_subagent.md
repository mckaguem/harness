---
name: "harness_core.tools.run_subagent.run_subagent"
description: "Spawn a named sub-agent and execute *task* on it."
source: "harness_core/tools/run_subagent.py"
---

Spawn a named sub-agent and execute *task* on it.

Args:
    sub_agent: Name of the sub-agent YAML (without extension).
    task: The task description to run.
    block: When ``True`` (default), runs synchronously and returns the
        :class:`ToolResult` directly (backward-compatible behaviour). When
        ``False``, launches the sub-agent in the BACKGROUND via the shared
        :class:`SubagentManager` and immediately returns a ``ToolResult``
        whose ``llm_text`` contains the background identifier
        (``"subagent-<n>"``) so the caller can later ``await_subagent`` it.

## Signature
```python
run_subagent(sub_agent: str, task: str, block: bool) -> ToolResult
```

## References
- [Module: harness_core.tools.run_subagent](harness_core_tools_run_subagent) - Parent module
