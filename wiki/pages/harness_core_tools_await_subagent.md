---
name: "harness_core.tools.await_subagent"
description: "await_subagent — block until a background sub-agent job completes."
source: "harness_core/tools/await_subagent.py"
---

await_subagent — block until a background sub-agent job completes.

The ``run_subagent(block=False)`` tool launches a sub-agent in the background
(via the shared :class:`~harness_core.tools.subagent_manager.SubagentManager`)
and returns a short identifier like ``"subagent-1"``. This tool waits for that
job to finish and returns its :class:`~harness_core.tools.tool_result.ToolResult`.

If ``identifier`` is omitted, it blocks until the *first* currently-running
background sub-agent completes and returns that result.

## References
- [await_subagent](harness_core_tools_await_subagent_await_subagent) - Block until a background sub-agent completes and return its result
- [Module Index](../index/harness_core_tools.md) - Parent module index
