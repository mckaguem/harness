---
name: "harness_core.agent.task_list.update_status"
description: "Update the status of a specific task."
source: "harness_core/agent/task_list.py"
---

Update the status of a specific task.

Args:
    task_id: The unique identifier of the task to update (1-indexed).
    status: The new status value (must be one of VALID_STATUSES).

Returns:
    A tuple ``(success, next_task_info)`` where ``success`` is True if the
    task was found and updated, and ``next_task_info`` describes what tasks
    remain.  ``next_task_info`` always points agents toward the next ID to act on.

Raises:
    ValueError: If the provided status is not in VALID_STATUSES.

## Signature
```python
update_status(self, task_id: int, status: str) -> tuple[bool, NextTaskInfo]
```

## References
- [Module: harness_core.agent.task_list](harness_core_agent_task_list) - Parent module
- [Class: TaskList](harness_core_agent_task_list_TaskList) - Parent class
