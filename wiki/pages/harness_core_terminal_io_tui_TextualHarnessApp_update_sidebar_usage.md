---
name: "harness_core.terminal_io.tui.update_sidebar_usage"
description: "Push the most recent usage summary to the right sidebar (thread-safe)."
source: "harness_core/terminal_io/tui.py"
---

Push the most recent usage summary to the right sidebar (thread-safe).

Marshals a single call onto the app thread that sets the stored usage
text and re-renders the sidebar above the task list.  This is only ever
invoked from the HarnessTUI controller after the app is bound and
running; it guards on the App's own ``is_running`` flag and wraps the
marshalled work in try/except so a stray call never raises (Textual's
``App`` does not expose an ``is_active`` property, which was the
original source of the reported crash).

## Signature
```python
update_sidebar_usage(self, text: str | None) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: TextualHarnessApp](harness_core_terminal_io_tui_TextualHarnessApp) - Parent class
