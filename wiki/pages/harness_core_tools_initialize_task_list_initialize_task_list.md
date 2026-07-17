---
name: "harness_core.tools.initialize_task_list.initialize_task_list"
description: "Initialize or reset the task list with a new set of tasks."
source: "harness_core/tools/initialize_task_list.py"
---

Initialize or reset the task list with a new set of tasks.

This tool clears any existing tasks and populates the current agent's TaskList instance
with a fresh set of pending tasks based on the provided descriptions.

Returns an error if there are currently incomplete (pending/in_progress) tasks. The caller
should either complete all tasks first or wait for them to be auto-cleared by update_task_status.

Args:
    tasks: A list of strings, each representing a task description.
           Each string becomes one task with auto-incremented IDs starting from 1.

Returns:
    On success: a :class:`ToolResult` containing status text for the LLM and
        JSON-encoded task list for machine consumption.
    On failure: a :class:`ToolResult` error (produced by :func:`make_error_result`).

Raises:
    ValueError: If the input is invalid (empty list, empty descriptions),
                or if there are incomplete tasks remaining in the current list.

## Signature
```python
initialize_task_list(agent: Any, tasks: list[str]) -> ToolResult
```

## References
- [Module: harness_core.tools.initialize_task_list](harness_core_tools_initialize_task_list) - Parent module
