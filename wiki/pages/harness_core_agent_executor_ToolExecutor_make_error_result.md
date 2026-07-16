---
name: "harness_core.agent.executor.make_error_result"
description: "Build a failure :class:`ToolResult` for a given error message."
source: "harness_core/agent/executor.py"
---

Build a failure :class:`ToolResult` for a given error message.

Args:
    func_name: The tool name that failed (used in the panel title).
    description: Human-readable error message to include as both LLM and display text.

Returns:
    A ``ToolResult`` with ``theme="error"`` carrying the error details.

## Signature
```python
make_error_result(self, func_name: str, description: str) -> ToolResult
```

## References
- [Module: harness_core.agent.executor](harness_core_agent_executor) - Parent module
- [Class: ToolExecutor](harness_core_agent_executor_ToolExecutor) - Parent class
