---
name: "harness_core.terminal_io.tui.StatusSpinner"
description: "A non-blocking animated "thinking" indicator for the message panel."
source: "harness_core/terminal_io/tui.py"
---

A non-blocking animated "thinking" indicator for the message panel.

Unlike Textual's built-in :class:`~textual.widgets.LoadingIndicator` this
widget does *not* swallow input events, so the user's ``TextArea`` stays
fully interactive while the agent is working.  It is docked to the bottom
of the messages panel and simply cycles through a small set of glyphs.

## Methods
- **__init__(self, *args, **kwargs) -> None** - No description
- **render(self) -> Text** - No description

## Class Variables
- `FRAMES`
- `LABEL`

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- Base class: `Static`
- [__init__](harness_core_terminal_io_tui_StatusSpinner___init__) - Method
- [render](harness_core_terminal_io_tui_StatusSpinner_render) - Method
- `FRAMES`
- `LABEL`
