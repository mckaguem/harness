---
name: "harness_core.terminal_io.tui.set_usage"
description: "Store the most recent LLM usage summary to render above the tasks."
source: "harness_core/terminal_io/tui.py"
---

Store the most recent LLM usage summary to render above the tasks.

``text`` is the ``format_speed`` summary string (or ``None`` to clear).
It is rendered on the next :meth:`refresh_tasks`.

## Signature
```python
set_usage(self, text: str | None) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: TaskListSidebar](harness_core_terminal_io_tui_TaskListSidebar) - Parent class
