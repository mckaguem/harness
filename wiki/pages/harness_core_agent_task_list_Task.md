---
name: "harness_core.agent.task_list.Task"
description: "Represents a single executable task within the agent's workflow."
source: "harness_core/agent/task_list.py"
---

Represents a single executable task within the agent's workflow.

## Methods
- **__post_init__(self)** - Validate that status is one of the allowed values
- **to_json(self) -> dict** - Serialize this task to a JSON-compatible dictionary with explicit ID

## Class Variables
- `id`: int
- `description`: str
- `status`: str

## References
- [Module: harness_core.agent.task_list](harness_core_agent_task_list) - Parent module
- [__post_init__](harness_core_agent_task_list_Task___post_init__) - Validate that status is one of the allowed values
- [to_json](harness_core_agent_task_list_Task_to_json) - Serialize this task to a JSON-compatible dictionary with explicit ID
- `id`: int
- `description`: str
- `status`: str - pending
