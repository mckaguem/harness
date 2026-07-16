---
name: "harness_core.terminal_io.display.display_tool_call"
description: "Print a tool-call panel showing the function name and its arguments."
source: "harness_core/terminal_io/display.py"
---

Print a tool-call panel showing the function name and its arguments.

Renders the call using ``display_message_panel`` with theme="info" and
result_type="markdown".  Arguments are displayed as key/value parameters
(the function name itself appears only in the title).

## Signature
```python
display_tool_call(func_name: str, args_str: str, summary: str | None) -> None
```

## References
- [Module: harness_core.terminal_io.display](harness_core_terminal_io_display) - Parent module
