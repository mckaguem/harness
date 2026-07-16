---
name: "harness_core.terminal_io.tui.write"
description: "Render ``renderable`` into the output pane (thread-safe)."
source: "harness_core/terminal_io/tui.py"
---

Render ``renderable`` into the output pane (thread-safe).

The output pane is a Textual :class:`~textual.containers.VerticalScroll`
of :class:`~textual.widgets.Static` wrappers (one per renderable).  This
lets tool calls become :class:`~textual.widgets.Collapsible` widgets
whose result can be appended *inside* them later, which a flat output
log cannot do.

## Signature
```python
write(self, renderable) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: HarnessTUI](harness_core_terminal_io_tui_HarnessTUI) - Parent class
