---
name: "harness_core.commands.tasks.cmd_tasks"
description: "Handle the /tasks command. Displays all tasks and their statuses."
source: "harness_core/commands/tasks.py"
---

Handle the /tasks command. Displays all tasks and their statuses.

Args:
    rest: Unused (kept for API consistency with other commands).
    agent: Optional pre-resolved Agent instance for testing. If ``None``,
           the active agent is read from :data:`CURRENT_AGENT`.

Returns:
    False to continue the parent loop (this is a display-only command).

## Signature
```python
cmd_tasks(rest: str, agent) -> bool | None
```

## References
- [Module: harness_core.commands.tasks](harness_core_commands_tasks) - Parent module
