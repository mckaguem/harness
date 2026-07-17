---
name: "harness_core.tools.run_subagent.run_subagents_parallel"
description: "Run several ``(sub_agent, task)`` pairs concurrently and return results in order."
source: "harness_core/tools/run_subagent.py"
---

Run several ``(sub_agent, task)`` pairs concurrently and return results in order.

Each call runs in its own worker thread (via :func:`run_subagent_async` /
``asyncio.to_thread``), giving every sub-agent its own worker thread.  Results are returned in the
same order as *calls*.

Args:
    calls: A list of ``(sub_agent, task)`` tuples.

Returns:
    A list of :class:`ToolResult` matching the order of *calls* (empty list
    if *calls* is empty).

## Signature
```python
run_subagents_parallel(calls: list[Tuple[str, str]]) -> list[ToolResult]
```

## References
- [Module: harness_core.tools.run_subagent](harness_core_tools_run_subagent) - Parent module
