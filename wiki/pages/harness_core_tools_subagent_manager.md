---
name: "harness_core.tools.subagent_manager"
description: "SubagentManager — registry/orchestrator for background sub-agent jobs."
source: "harness_core/tools/subagent_manager.py"
---

SubagentManager — registry/orchestrator for background sub-agent jobs.

This module owns the "in-flight background sub-agent" lifecycle:

* ``launch`` submits a sub-agent job to a worker thread, returns a short
  identifier such as
  ``"subagent-1"``, and enforces a maximum concurrency limit.
* ``await_one`` blocks until a specific (or the first completed) background job
  finishes and returns its :class:`~harness_core.tools.tool_result.ToolResult`.

It is intentionally decoupled from the synchronous ``run_subagent`` path so that
the existing behaviour (``block=True``) is untouched. A module-level singleton
``manager`` is shared by the ``run_subagent(block=False)`` tool path and the
``await_subagent`` tool.

## References
- [SubagentManager](harness_core_tools_subagent_manager_SubagentManager) - Track and orchestrate background sub-agent jobs
  - [__init__](harness_core_tools_subagent_manager_SubagentManager___init__) - Method
  - [launch](harness_core_tools_subagent_manager_SubagentManager_launch) - Start *sub_agent*/*task* in the background and return an identifier
  - [await_one](harness_core_tools_subagent_manager_SubagentManager_await_one) - Block until a background job finishes and return its ToolResult
  - [active_count](harness_core_tools_subagent_manager_SubagentManager_active_count) - Return the number of currently in-flight background jobs
  - [is_running](harness_core_tools_subagent_manager_SubagentManager_is_running) - Return True if *identifier* refers to a still-active background job
- [DEFAULT_MAX_CONCURRENT](harness_core_tools_subagent_manager_DEFAULT_MAX_CONCURRENT) - Constant
- [Module Index](../index/harness_core_tools.md) - Parent module index
