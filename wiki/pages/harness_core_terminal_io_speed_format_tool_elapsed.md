---
name: "harness_core.terminal_io.speed.format_tool_elapsed"
description: "Format elapsed time for a tool execution as a compact string."
source: "harness_core/terminal_io/speed.py"
---

Format elapsed time for a tool execution as a compact string.

Args:
    elapsed_seconds: Time in seconds (float).

Returns:
    A formatted string like ``⏱ 1.2s`` or ``⏱ 450ms``.

## Signature
```python
format_tool_elapsed(elapsed_seconds: float) -> str
```

## References
- [Module: harness_core.terminal_io.speed](harness_core_terminal_io_speed) - Parent module
