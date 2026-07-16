---
name: "harness_core.agent.task_list._emit"
description: "Publish a tasklist event if an event loop is running."
source: "harness_core/agent/task_list.py"
---

Publish a tasklist event if an event loop is running.

In non-async contexts (e.g. unit tests) there is no running loop, so
we skip emission — no listeners will be present anyway.

## Signature
```python
_emit(self, topic: str) -> None
```

## References
- [Module: harness_core.agent.task_list](harness_core_agent_task_list) - Parent module
- [Class: TaskList](harness_core_agent_task_list_TaskList) - Parent class
