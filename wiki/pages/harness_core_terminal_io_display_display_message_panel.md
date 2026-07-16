---
name: "harness_core.terminal_io.display.display_message_panel"
description: "Display a Rich panel with the given text, styled by theme."
source: "harness_core/terminal_io/display.py"
---

Display a Rich panel with the given text, styled by theme.

Shared rendering logic for tool-result panels and ad-hoc command output.

Args:
    text: The content to display inside the panel. Truncated after 5 lines
          unless ``theme == "status"`` (e.g. task lists).
    theme: One of ``"error"``, ``"status"``, ``"info"``, ``"read"``,
            ``"write"``, ``"command"`` — selects the panel border color.
    title: Custom panel title. Falls back to a default if empty.
    result_type: The syntax-highlighting language tag (e.g. ``"markdown"``,
                 ``"json"``, ``"text"``).
    return_renderable: When True, return the built ``Panel`` instead of
            writing it (used by :func:`display_tool_call` so the panel can
            be reused/extended later).

Returns:
    The built ``Panel`` when ``return_renderable`` is True, else ``None``.

## Signature
```python
display_message_panel(text: str, theme: str, title: str, result_type: str, return_renderable: bool) -> 'RenderableType | None'
```

## References
- [Module: harness_core.terminal_io.display](harness_core_terminal_io_display) - Parent module
