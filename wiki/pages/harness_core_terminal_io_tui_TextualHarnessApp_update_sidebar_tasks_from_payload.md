---
name: "harness_core.terminal_io.tui.update_sidebar_tasks_from_payload"
description: "Push a TaskListPayload snapshot to the right sidebar (thread-safe)."
source: "harness_core/terminal_io/tui.py"
---

Push a TaskListPayload snapshot to the right sidebar (thread-safe).

Marshals a single call onto the app thread that re-renders the sidebar
from the event payload.  Guards on the App's own ``is_running`` flag and
wraps the marshalled work in try/except so a stray call never raises.

## Signature
```python
update_sidebar_tasks_from_payload(self, payload: TaskListPayload) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: TextualHarnessApp](harness_core_terminal_io_tui_TextualHarnessApp) - Parent class
