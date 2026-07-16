---
name: "harness_core.terminal_io.prompt"
description: "User input prompt with readline support (arrow keys, history)."
source: "harness_core/terminal_io/prompt.py"
---

User input prompt with readline support (arrow keys, history).

When a textual TUI is active, :func:`prompt_user` delegates to the TUI
controller's blocking :meth:`~terminal_io.tui.HarnessTUI.prompt`, which reads
from the on-screen ``TextArea``.  Otherwise the original ``prompt_toolkit``
multi-line session (with ``~/.history`` persistence) is used unchanged.

## References
- [prompt_user](harness_core_terminal_io_prompt_prompt_user) - Display the user prompt and read *multi-line* input
- [Module Index](../index/harness_core_terminal_io.md) - Parent module index
