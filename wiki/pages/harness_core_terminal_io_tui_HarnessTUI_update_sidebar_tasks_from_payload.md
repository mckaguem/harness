---
name: "harness_core.terminal_io.tui.update_sidebar_tasks_from_payload"
description: "Push a TaskListPayload snapshot to the right sidebar (thread-safe)."
source: "harness_core/terminal_io/tui.py"
---

Push a TaskListPayload snapshot to the right sidebar (thread-safe).

No-op unless the TUI is active; otherwise delegates to the running
:class:`TextualHarnessApp`, which marshals the update onto the app
thread.

## Signature
```python
update_sidebar_tasks_from_payload(self, payload: TaskListPayload) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: HarnessTUI](harness_core_terminal_io_tui_HarnessTUI) - Parent class
