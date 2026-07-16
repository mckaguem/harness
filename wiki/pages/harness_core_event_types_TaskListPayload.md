---
name: "harness_core.event_types.TaskListPayload"
description: "Event payload containing a complete task list snapshot."
source: "harness_core/event_types.py"
---

Event payload containing a complete task list snapshot.

This payload is emitted when the task list changes, providing subscribers
with the full current state of all tasks. It's designed to be lightweight
and serializable for use across process boundaries or in logs.

Attributes:
    tasks: List of TaskInfo objects representing each task's current state.
    total_tasks: Total number of tasks in the list.
    completed_tasks: Number of tasks with status 'completed' or 'failed'.
    has_incomplete: Whether there are any pending or in_progress tasks.

## Methods
- **from_task_list(cls, task_list: 'TaskList') -> 'TaskListPayload'** - Create a TaskListPayload from a TaskList instance
- **to_dict(self) -> dict[str, Any]** - Convert the payload to a dictionary for serialization

## Class Variables
- `tasks`: list[TaskInfo]
- `total_tasks`: int
- `completed_tasks`: int
- `has_incomplete`: bool

## References
- [Module: harness_core.event_types](harness_core_event_types) - Parent module
- Base class: `EventPayload`
- [from_task_list](harness_core_event_types_TaskListPayload_from_task_list) - Create a TaskListPayload from a TaskList instance
- [to_dict](harness_core_event_types_TaskListPayload_to_dict) - Convert the payload to a dictionary for serialization
- `tasks`: list[TaskInfo]
- `total_tasks`: int
- `completed_tasks`: int
- `has_incomplete`: bool
