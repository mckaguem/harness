---
name: "harness_core.terminal_io.display._tui_write"
description: "Route a renderable to the active TUI, or fall back to ``console``."
source: "harness_core/terminal_io/display.py"
---

Route a renderable to the active TUI, or fall back to ``console``.

When a textual TUI owns the screen the renderable is emitted into the
output pane (a VerticalScroll of Static widgets; tool calls become
Collapsible widgets).  Otherwise we print it on the
``@patch("harness_core.terminal_io.display.console")`` tests valid.

## Signature
```python
_tui_write(renderable) -> None
```

## References
- [Module: harness_core.terminal_io.display](harness_core_terminal_io_display) - Parent module
