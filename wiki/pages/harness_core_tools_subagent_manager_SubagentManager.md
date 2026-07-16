---
name: "harness_core.tools.subagent_manager.SubagentManager"
description: "Track and orchestrate background sub-agent jobs."
source: "harness_core/tools/subagent_manager.py"
---

Track and orchestrate background sub-agent jobs.

## Methods
- **__init__(self, max_concurrent: int) -> None** - No description
- **launch(self, sub_agent: str, task: str) -> str** - Start *sub_agent*/*task* in the background and return an identifier
- **await_one(self, identifier: str | None, timeout: float | None) -> ToolResult** - Block until a background job finishes and return its ToolResult
- **active_count(self) -> int** - Return the number of currently in-flight background jobs
- **is_running(self, identifier: str) -> bool** - Return True if *identifier* refers to a still-active background job

## Class Variables
None

## References
- [Module: harness_core.tools.subagent_manager](harness_core_tools_subagent_manager) - Parent module
- [__init__](harness_core_tools_subagent_manager_SubagentManager___init__) - Method
- [launch](harness_core_tools_subagent_manager_SubagentManager_launch) - Start *sub_agent*/*task* in the background and return an identifier
- [await_one](harness_core_tools_subagent_manager_SubagentManager_await_one) - Block until a background job finishes and return its ToolResult
- [active_count](harness_core_tools_subagent_manager_SubagentManager_active_count) - Return the number of currently in-flight background jobs
- [is_running](harness_core_tools_subagent_manager_SubagentManager_is_running) - Return True if *identifier* refers to a still-active background job
