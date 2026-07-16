---
name: "harness_core.event_types.from_task_list"
description: "Create a TaskListPayload from a TaskList instance."
source: "harness_core/event_types.py"
---

Create a TaskListPayload from a TaskList instance.

This factory method extracts the relevant state from a TaskList
and creates a serializable payload suitable for event emission.

Args:
    task_list: The TaskList instance to convert.

Returns:
    A new TaskListPayload containing the task list's current state.

## Signature
```python
from_task_list(cls, task_list: 'TaskList') -> 'TaskListPayload'
```

## References
- [Module: harness_core.event_types](harness_core_event_types) - Parent module
- [Class: TaskListPayload](harness_core_event_types_TaskListPayload) - Parent class
