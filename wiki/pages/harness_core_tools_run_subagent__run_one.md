---
name: "harness_core.tools.run_subagent._run_one"
description: "Spawn a single named sub-agent and execute *task* on it (worker body)."
source: "harness_core/tools/run_subagent.py"
---

Spawn a single named sub-agent and execute *task* on it (worker body).

Contains the exact synchronous work previously done by :func:`run_subagent`.
Designed to run inside its own worker thread (via ``asyncio.to_thread``).

## Signature
```python
_run_one(sub_agent: str, task: str) -> ToolResult
```

## References
- [Module: harness_core.tools.run_subagent](harness_core_tools_run_subagent) - Parent module
