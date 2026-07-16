---
name: "harness_core.terminal_io.tui.begin_tool_panel"
description: "Create a collapsed-by-default ``Collapsible`` for a tool call."
source: "harness_core/terminal_io/tui.py"
---

Create a collapsed-by-default ``Collapsible`` for a tool call.

Called from :func:`terminal_io.display.display_tool_call` when the TUI is
active (in addition to, not instead of, the classic ``write``).  The
collapsible's title is the panel title (``"Tool: <name>"``), and its
initial child is the tool-call renderable.  The widget is pushed onto
``_tool_stack`` so the matching :meth:`complete_tool_panel` (which is
always emitted immediately after in the agent loop) can append the
result into this same collapsible.

## Signature
```python
begin_tool_panel(self, title: str, call_renderable) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: HarnessTUI](harness_core_terminal_io_tui_HarnessTUI) - Parent class
