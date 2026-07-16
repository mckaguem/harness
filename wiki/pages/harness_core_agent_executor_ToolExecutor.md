---
name: "harness_core.agent.executor.ToolExecutor"
description: "Handles tool dispatching and result formatting for an agent."
source: "harness_core/agent/executor.py"
---

Handles tool dispatching and result formatting for an agent.

Encapsulates the mechanics of calling tools via the dispatcher registry
and wrapping results (success or failure) in :class:`ToolResult` objects.
This keeps tool execution concerns separate from conversation orchestration.

## Methods
- **__init__(self, agent_name: str)** - No description
- **execute(self, func_name: str, args: dict)** - Dispatch a tool call by name and return its result (ToolResult or raise)
- **make_error_result(self, func_name: str, description: str) -> ToolResult** - Build a failure :class:`ToolResult` for a given error message
- **make_submit_results_block(self, has_incomplete_tasks: bool) -> dict | None** - Return a blocking message payload if submit_results should be denied

## Class Variables
None

## References
- [Module: harness_core.agent.executor](harness_core_agent_executor) - Parent module
- [__init__](harness_core_agent_executor_ToolExecutor___init__) - Method
- [execute](harness_core_agent_executor_ToolExecutor_execute) - Dispatch a tool call by name and return its result (ToolResult or raise)
- [make_error_result](harness_core_agent_executor_ToolExecutor_make_error_result) - Build a failure :class:`ToolResult` for a given error message
- [make_submit_results_block](harness_core_agent_executor_ToolExecutor_make_submit_results_block) - Return a blocking message payload if submit_results should be denied
