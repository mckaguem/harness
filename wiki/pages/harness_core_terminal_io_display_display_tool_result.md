---
name: "harness_core.terminal_io.display.display_tool_result"
description: "Print a truncated tool-result panel with syntax highlighting."
source: "harness_core/terminal_io/display.py"
---

Print a truncated tool-result panel with syntax highlighting.

When a textual TUI is active and the result corresponds to the most
recently displayed tool call (see :func:`display_tool_call`), the result is
appended *inside* that same panel rather than rendered as a fresh panel —
a horizontal rule separator is drawn between the call and the result.  When
no matching tool-call panel is tracked (classic REPL, or a result that is
not paired with an immediate call), the result is shown in its own panel as
before.

Args:
    func_name: Name of the tool that produced the result.
    result: A ToolResult object, or None if using individual parameters.
    result_title: Title override from the ToolResult object, or None.
    result_display_text: The display text content of the ToolResult.
    result_theme: Color/theme string for rendering (e.g. "info", "error").
    result_type_tag: Type tag from the ToolResult, defaults to "text".

## Signature
```python
display_tool_result(func_name: str, result: Optional[object], result_title: Optional[str], result_display_text: Optional[str], result_theme: Optional[str], result_type_tag: Optional[str]) -> None
```

## References
- [Module: harness_core.terminal_io.display](harness_core_terminal_io_display) - Parent module
