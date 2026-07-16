---
name: "harness_core.tools.run_subagent._run_one"
description: "Spawn a single named sub-agent and execute *task* on it (worker body)."
source: "harness_core/tools/run_subagent.py"
---

Spawn a single named sub-agent and execute *task* on it (worker body).

Contains the exact synchronous work previously done by :func:`run_subagent`.
Designed to run inside its own worker thread (via ``asyncio.to_thread``) so
that each sub-agent gets its OWN copy of the ``CURRENT_AGENT`` contextvar —
ContextVars are copied per thread, so concurrent sub-agents cannot clobber
each other's or the caller's agent binding.

NOTE on CURRENT_AGENT context isolation:

Each :class:`Agent.__init__` calls ``CURRENT_AGENT.set(self)``, which means
spawning a sub-agent temporarily overwrites the active agent's entry in this
module-level ``contextvars.ContextVar``.  If we don't restore it before
returning, any subsequent tool call inside the *calling* agent's
handle_prompt loop (such as ``update_task_status`` or ``initialize_task_list``)
would look at the sub-agent's empty task list and report "Task with ID X not
found" — even though the calling agent clearly has a task with that ID.

To prevent this, we save the active CURRENT_AGENT value before spawning and
restore it via a ``finally`` block that covers **every** possible exit path
(early returns inside the loop, exceptions during spawn, etc.).  Because this
runs inside a worker thread, the restore only affects that thread's context;
the caller's thread context is untouched.

## Signature
```python
_run_one(sub_agent: str, task: str) -> ToolResult
```

## References
- [Module: harness_core.tools.run_subagent](harness_core_tools_run_subagent) - Parent module
