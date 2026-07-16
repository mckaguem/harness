---
name: "harness_core.terminal_io.tui.show_spinner"
description: "Reveal the spinner so the user knows the agent is working."
source: "harness_core/terminal_io/tui.py"
---

Reveal the spinner so the user knows the agent is working.

Thread-safe: the loop/worker thread may call this while the spinner
widget lives on the app thread; the visibility change is marshalled
through ``app.call_from_thread``. If called from the app thread
directly, runs synchronously.

## Signature
```python
show_spinner(self) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: HarnessTUI](harness_core_terminal_io_tui_HarnessTUI) - Parent class
