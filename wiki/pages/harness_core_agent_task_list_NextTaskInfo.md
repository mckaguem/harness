---
name: "harness_core.agent.task_list.NextTaskInfo"
description: "Information about the next uncompleted task, returned by update_status."
source: "harness_core/agent/task_list.py"
---

Information about the next uncompleted task, returned by update_status.

Used to guide agents toward the correct (1-indexed) task ID and to signal
when all tasks are complete so the caller can clear the list.

## Methods
None

## Class Variables
- `has_next`: bool
- `id`: int | None
- `description`: str
- `status`: str
- `all_complete`: bool
- `message`: str

## References
- [Module: harness_core.agent.task_list](harness_core_agent_task_list) - Parent module
- `has_next`: bool
- `id`: int | None
- `description`: str
- `status`: str
- `all_complete`: bool
- `message`: str
