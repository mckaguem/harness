---
name: "harness_core.agent.task_list.__init__"
description: "Initialize an empty TaskList instance."
source: "harness_core/agent/task_list.py"
---

Initialize an empty TaskList instance.

Args:
    id: Optional identifier. If provided, the TaskList's id is set to
        ``f"TaskList.{id}"`` (saved to ``self`` with the ``TaskList.``
        prefix). If None, a unique id is generated.
    sender_id: Optional id used as the event ``sender`` when this
        TaskList publishes events. Normally this is the owning agent's
        id (e.g. ``Agent.main``). If None, defaults to ``self.id``.

## Signature
```python
__init__(self, id: str | None, sender_id: str | None)
```

## References
- [Module: harness_core.agent.task_list](harness_core_agent_task_list) - Parent module
- [Class: TaskList](harness_core_agent_task_list_TaskList) - Parent class
