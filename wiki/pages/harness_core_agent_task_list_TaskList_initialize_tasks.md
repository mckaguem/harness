---
name: "harness_core.agent.task_list.initialize_tasks"
description: "Clear existing tasks and populate with a new list."
source: "harness_core/agent/task_list.py"
---

Clear existing tasks and populate with a new list.

Raises ValueError if there are currently incomplete (pending/in_progress)
tasks remaining. Call :meth:`reset` to clear the list before re-initializing
in that case.

Args:
    tasks: A list of task description strings. Each string becomes
           the description for a new Task object with auto-incremented
           IDs starting from 1 and status set to "pending".

Raises:
    ValueError: If any task description is empty or None,
                or if there are incomplete tasks in the current list.

## Signature
```python
initialize_tasks(self, tasks: list[str]) -> None
```

## References
- [Module: harness_core.agent.task_list](harness_core_agent_task_list) - Parent module
- [Class: TaskList](harness_core_agent_task_list_TaskList) - Parent class
