---
name: "harness_core.terminal_io.tui.prompt"
description: "Block the calling (loop) thread until the user submits input."
source: "harness_core/terminal_io/tui.py"
---

Block the calling (loop) thread until the user submits input.

Mirrors the ``prompt_toolkit`` contract: returns the assembled text
(newlines preserved).  An empty submission returns ``""`` (equivalent to
the classic Ctrl+D-on-blank behaviour).

## Signature
```python
prompt(self, prompt_str: str) -> str
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- [Class: HarnessTUI](harness_core_terminal_io_tui_HarnessTUI) - Parent class
