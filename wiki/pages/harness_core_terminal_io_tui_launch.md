---
name: "harness_core.terminal_io.tui.launch"
description: "Launch the textual TUI and drive ``user_loop`` on a worker thread."
source: "harness_core/terminal_io/tui.py"
---

Launch the textual TUI and drive ``user_loop`` on a worker thread.

Args:
    agent: An initialized :class:`~agent.core.Agent` instance.
    on_exit: Optional callback invoked when the loop ends (see
        :func:`agent.loop.user_loop`).

## Signature
```python
launch(agent, on_exit) -> None
```

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
