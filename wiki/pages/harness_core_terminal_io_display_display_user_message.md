---
name: "harness_core.terminal_io.display.display_user_message"
description: "Echo the user's own typed message into the output pane."
source: "harness_core/terminal_io/display.py"
---

Echo the user's own typed message into the output pane.

In the classic (non-TUI) REPL, ``prompt_toolkit`` renders the typed text
directly onto the terminal, so the user sees what they entered.  In the
textual TUI the input lives in a separate ``TextArea`` that is cleared on
submit and never copied into the output pane — without this
echo, the user's messages never appear alongside the agent's responses.

The message is wrapped in a :class:`~rich.text.Text` (not a markup string)
so any ``[tag]``-style characters the user types are rendered verbatim
rather than interpreted as Rich markup.

## Signature
```python
display_user_message(message: str) -> None
```

## References
- [Module: harness_core.terminal_io.display](harness_core_terminal_io_display) - Parent module
