---
name: "harness_core.terminal_io.tui.refresh_tasks_from_payload"
description: "Re-render the task list from a TaskListPayload (event-driven)."
source: "harness_core/terminal_io/tui.py"
---

Re-render the task list from a TaskListPayload (event-driven).

Mirrors :meth:`refresh_tasks` but sources the task rows from an event
payload rather than the agent's live TaskList, so sidebar updates can be
driven directly by the TaskList EventBus.

## Signature
```python
refresh_tasks_from_payload(self, payload: TaskListPayload) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: TaskListSidebar](harness_core_terminal_io_tui_TaskListSidebar) - Parent class
