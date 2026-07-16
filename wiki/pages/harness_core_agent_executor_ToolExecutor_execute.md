---
name: "harness_core.agent.executor.execute"
description: "Dispatch a tool call by name and return its result (ToolResult or raise)."
source: "harness_core/agent/executor.py"
---

Dispatch a tool call by name and return its result (ToolResult or raise).

Calls the registered tool function via :func:`tools.dispatcher.dispatch`.

Args:
    func_name: The tool function name (e.g. ``"execute_bash"``).
    args: Keyword arguments to pass to the tool function.

Returns:
    A :class:`ToolResult` from the successful tool execution.

Raises:
    KeyError: If *func_name* is not registered in the dispatcher.
    Exception: Re-raised if the tool raises an unexpected error — callers
               should catch this and wrap it in a ``ToolResult`` of their own.

## Signature
```python
execute(self, func_name: str, args: dict)
```

## References
- [Module: harness_core.agent.executor](harness_core_agent_executor) - Parent module
- [Class: ToolExecutor](harness_core_agent_executor_ToolExecutor) - Parent class
