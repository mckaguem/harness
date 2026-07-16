---
name: "harness_core.terminal_io.tui.complete_tool_panel"
description: "Append a tool result into the most recent tool-call collapsible."
source: "harness_core/terminal_io/tui.py"
---

Append a tool result into the most recent tool-call collapsible.

Called from :func:`terminal_io.display.display_tool_result` when the TUI
is active.  Pops the most recent collapsible off ``_tool_stack`` and
mounts the result renderable inside it, after a ``Rule`` separator, so
the result is inline (not a separate panel).  Matches the stack-pop in
``begin_tool_panel`` because the agent loop always emits a TOOL_RESULT
immediately after its TOOL_CALL.

## Signature
```python
complete_tool_panel(self, result_renderable) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: HarnessTUI](harness_core_terminal_io_tui_HarnessTUI) - Parent class
