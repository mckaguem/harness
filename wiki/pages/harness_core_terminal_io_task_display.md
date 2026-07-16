---
name: "harness_core.terminal_io.task_display"
description: "Task display utilities for rendering TaskList as formatted Markdown."
source: "harness_core/terminal_io/task_display.py"
---

Task display utilities for rendering TaskList as formatted Markdown.

This module separates the view layer (formatting) from the model (TaskList),
enabling cleaner separation of concerns and easier testing.

## References
- [render_task_list_markdown](harness_core_terminal_io_task_display_render_task_list_markdown) - Render the current task list state as a formatted markdown string
- [render_task_list_markdown_from_payload](harness_core_terminal_io_task_display_render_task_list_markdown_from_payload) - Render a :class:`TaskListPayload` (event payload) as markdown
- [Module Index](../index/harness_core_terminal_io.md) - Parent module index
