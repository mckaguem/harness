---
name: "harness_core.terminal_io.display"
description: "High-level display helpers using Rich for rendering."
source: "harness_core/terminal_io/display.py"
---

High-level display helpers using Rich for rendering.

These helpers build Rich renderables (``Panel`` / ``Markdown`` / ``Syntax``)
exactly as before.  When a textual TUI is active each renderable is routed to
the app's output pane (:class:`~textual.containers.VerticalScroll` of
:class:`~textual.widgets.Static` widgets, with tool calls as
:class:`~textual.widgets.Collapsible` widgets) via
:func:`terminal_io.tui.get_tui().write`; when no TUI is active it falls back
to the module-level :data:`console` so that callers outside the TUI (and the
existing test-suite, which patches this ``console``) keep working unchanged.

## References
- [_tui_write](harness_core_terminal_io_display__tui_write) - Route a renderable to the active TUI, or fall back to ``console``
- [print_system](harness_core_terminal_io_display_print_system) - Print a system-level notification panel
- [display_tool_call](harness_core_terminal_io_display_display_tool_call) - Print a tool-call panel showing the function name and its arguments
- [_theme_border](harness_core_terminal_io_display__theme_border) - Return a Rich border style string for the given theme
- [display_message_panel](harness_core_terminal_io_display_display_message_panel) - Display a Rich panel with the given text, styled by theme
- [display_tool_result](harness_core_terminal_io_display_display_tool_result) - Print a truncated tool-result panel with syntax highlighting
- [reset_pending_tool_panel](harness_core_terminal_io_display_reset_pending_tool_panel) - Forget the most recently displayed tool-call panel
- [display_error](harness_core_terminal_io_display_display_error) - Print an error message in red
- [display_user_message](harness_core_terminal_io_display_display_user_message) - Echo the user's own typed message into the output pane
- [_combine_reasoning](harness_core_terminal_io_display__combine_reasoning) - Prepend reasoning/thinking above a horizontal separator, then the body
- [display_agent_response](harness_core_terminal_io_display_display_agent_response) - Display the agent's response safely
- [display_turn_stats](harness_core_terminal_io_display_display_turn_stats) - Push the most recent turn's usage + elapsed time into the right sidebar
- [_LAST_TOOL_PANEL](harness_core_terminal_io_display__LAST_TOOL_PANEL) - Constant
- [Module Index](../index/harness_core_terminal_io.md) - Parent module index
