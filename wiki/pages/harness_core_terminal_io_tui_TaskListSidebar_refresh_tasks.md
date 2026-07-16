---
name: "harness_core.terminal_io.tui.refresh_tasks"
description: "Re-render the sidebar."
source: "harness_core/terminal_io/tui.py"
---

Re-render the sidebar.

The usage summary (if set) is always shown at the top, above the task
list.  The task list renders below it whenever one exists (even when
empty after completion); if no task list is available yet, only the
usage block is shown.

## Signature
```python
refresh_tasks(self) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: TaskListSidebar](harness_core_terminal_io_tui_TaskListSidebar) - Parent class
