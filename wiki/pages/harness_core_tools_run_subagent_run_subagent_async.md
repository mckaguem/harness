---
name: "harness_core.tools.run_subagent.run_subagent_async"
description: "Run a single sub-agent off the event loop, returning a :class:`ToolResult`."
source: "harness_core/tools/run_subagent.py"
---

Run a single sub-agent off the event loop, returning a :class:`ToolResult`.

Offloads the synchronous :func:`_run_one` to a worker thread via
``asyncio.to_thread`` so that multiple sub-agents can run concurrently
(each in its own thread/context) when gathered.

## Signature
```python
run_subagent_async(sub_agent: str, task: str) -> ToolResult
```

## References
- [Module: harness_core.tools.run_subagent](harness_core_tools_run_subagent) - Parent module
