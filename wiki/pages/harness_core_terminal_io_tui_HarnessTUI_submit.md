---
name: "harness_core.terminal_io.tui.submit"
description: "Resolve a pending :meth:`prompt` with the current input text."
source: "harness_core/terminal_io/tui.py"
---

Resolve a pending :meth:`prompt` with the current input text.

Called from the app thread (e.g. the Ctrl+Enter key handler) where the
``TextArea`` is a live, mounted widget.  After capturing the text we
immediately clear the box so the submitted content does not linger in
the input for the rest of the turn; ``_arm_input`` also clears/focuses
on the next prompt, but that only happens once the agent responds.

## Signature
```python
submit(self) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: HarnessTUI](harness_core_terminal_io_tui_HarnessTUI) - Parent class
