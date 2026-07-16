---
name: "harness_core.agent.executor"
description: "Tool executor — handles dispatch, result formatting, and error wrapping."
source: "harness_core/agent/executor.py"
---

Tool executor — handles dispatch, result formatting, and error wrapping.

## References
- [ToolExecutor](harness_core_agent_executor_ToolExecutor) - Handles tool dispatching and result formatting for an agent
  - [__init__](harness_core_agent_executor_ToolExecutor___init__) - Method
  - [execute](harness_core_agent_executor_ToolExecutor_execute) - Dispatch a tool call by name and return its result (ToolResult or raise)
  - [make_error_result](harness_core_agent_executor_ToolExecutor_make_error_result) - Build a failure :class:`ToolResult` for a given error message
  - [make_submit_results_block](harness_core_agent_executor_ToolExecutor_make_submit_results_block) - Return a blocking message payload if submit_results should be denied
- [Module Index](../index/harness_core_agent.md) - Parent module index
