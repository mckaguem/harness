---
name: "harness_core.agent.executor.make_submit_results_block"
description: "Return a blocking message payload if submit_results should be denied."
source: "harness_core/agent/executor.py"
---

Return a blocking message payload if submit_results should be denied.

When there are incomplete tasks (pending or in_progress), returns a
dictionary containing the blocked message content and a corresponding
``ToolResult`` so callers can inject the block into the conversation
without duplicating formatting logic.

Args:
    has_incomplete_tasks: Whether :meth:`TaskList.has_incomplete_tasks` returned True.

Returns:
    A dict ``{"role": "user", "content": "...", "result": ToolResult(...)}`` if blocking,
    or ``None`` if submit_results should proceed normally (no incomplete tasks).

## Signature
```python
make_submit_results_block(self, has_incomplete_tasks: bool) -> dict | None
```

## References
- [Module: harness_core.agent.executor](harness_core_agent_executor) - Parent module
- [Class: ToolExecutor](harness_core_agent_executor_ToolExecutor) - Parent class
