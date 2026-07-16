---
name: "harness_core.agent.task_list.has_incomplete_tasks"
description: "Check if there are any tasks that haven't been completed or failed."
source: "harness_core/agent/task_list.py"
---

Check if there are any tasks that haven't been completed or failed.

Kept as a thin wrapper around ``not self.all_complete()`` plus an empty-list
guard, for callers (e.g. the core loop terminator) that only need the boolean.

## Signature
```python
has_incomplete_tasks(self) -> bool
```

## References
- [Module: harness_core.agent.task_list](harness_core_agent_task_list) - Parent module
- [Class: TaskList](harness_core_agent_task_list_TaskList) - Parent class
