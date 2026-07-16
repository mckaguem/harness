---
name: "harness_core.tools.update_task_status.summary"
description: "Return a one-line summary string for the update_task_status action."
source: "harness_core/tools/update_task_status.py"
---

Return a one-line summary string for the update_task_status action.

Args:
    task_id: Integer ID of the task to update (1-indexed).
    status: New status value.

Returns:
    A one-line summary string in the format:
    "update task status: task {task_id} set to '{status}'"

## Signature
```python
summary(task_id: int, status: str) -> str
```

## References
- [Module: harness_core.tools.update_task_status](harness_core_tools_update_task_status) - Parent module
