---
name: "harness_core.tools.update_task_status.update_task_status"
description: "Update the status of a specific task."
source: "harness_core/tools/update_task_status.py"
---

Update the status of a specific task.

Updates the status field of a Task object in the current agent's TaskList instance.
The new status must be one of VALID_STATUSES (pending, in_progress, completed, failed).

On success this also returns structured info about what tasks remain:
  - ``next_task_id``: 1-indexed ID of the next pending/in_progress task to work on,
    or None if every task is done.
  - ``all_complete``: True when every task has been completed or failed.

When ``all_complete`` is True, the agent's TaskList is reset so future injections
stop including stale state and a message indicating completion is returned.

Args:
    task_id: Integer ID of the task to update (1-indexed).
    status: New status value (must be one of VALID_STATUSES).

Returns:
    On success: a :class:`ToolResult` containing status text for the LLM and
        JSON-encoded remaining-task information for machine consumption.
    On failure: a :class:`ToolResult` error (produced by :func:`make_error_result`).

Raises:
    ValueError: If the provided status is not in VALID_STATUSES.

## Signature
```python
update_task_status(task_id: int, status: str, ctx: ToolContext | None) -> ToolResult
```

## References
- [Module: harness_core.tools.update_task_status](harness_core_tools_update_task_status) - Parent module
