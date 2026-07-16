---
name: "harness_core.terminal_io.tui.write_count"
description: "Number of times :meth:`write` committed to the output pane."
source: "harness_core/terminal_io/tui.py"
---

Number of times :meth:`write` committed to the output pane.

Useful for tests that want to assert a render happened without poking
at output-pane internals.

## Signature
```python
write_count(self) -> int
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: HarnessTUI](harness_core_terminal_io_tui_HarnessTUI) - Parent class
