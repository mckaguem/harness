---
name: "harness_core.terminal_io.display.reset_pending_tool_panel"
description: "Forget the most recently displayed tool-call panel."
source: "harness_core/terminal_io/display.py"
---

Forget the most recently displayed tool-call panel.

Called when an unpaired event occurs (e.g. an ``ERROR``) so a later tool
result does not incorrectly fold into a call that has no corresponding
result.

## Signature
```python
reset_pending_tool_panel() -> None
```

## References
- [Module: harness_core.terminal_io.display](harness_core_terminal_io_display) - Parent module
