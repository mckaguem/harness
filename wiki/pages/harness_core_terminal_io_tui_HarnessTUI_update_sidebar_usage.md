---
name: "harness_core.terminal_io.tui.update_sidebar_usage"
description: "Push the most recent usage summary to the right sidebar."
source: "harness_core/terminal_io/tui.py"
---

Push the most recent usage summary to the right sidebar.

No-op unless the TUI is active; otherwise delegates to the running
:class:`TextualHarnessApp`, which marshals the update onto the app
thread.

## Signature
```python
update_sidebar_usage(self, text: str | None) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: HarnessTUI](harness_core_terminal_io_tui_HarnessTUI) - Parent class
