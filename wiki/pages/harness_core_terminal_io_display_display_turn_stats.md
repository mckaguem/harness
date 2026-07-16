---
name: "harness_core.terminal_io.display.display_turn_stats"
description: "Push the most recent turn's usage + elapsed time into the right sidebar."
source: "harness_core/terminal_io/display.py"
---

Push the most recent turn's usage + elapsed time into the right sidebar.

Only the latest stats are shown (the sidebar overwrites its stats each call).

## Signature
```python
display_turn_stats(response: dict | None, context_length: int, elapsed_seconds: float | None) -> None
```

## References
- [Module: harness_core.terminal_io.display](harness_core_terminal_io_display) - Parent module
