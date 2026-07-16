---
name: "harness_core.terminal_io.task_display.render_task_list_markdown_from_payload"
description: "Render a :class:`TaskListPayload` (event payload) as markdown."
source: "harness_core/terminal_io/task_display.py"
---

Render a :class:`TaskListPayload` (event payload) as markdown.

Produces the same checkbox-list markdown as :func:`render_task_list_markdown`
but sourced from the serializable ``TaskInfo`` list carried by the event
payload rather than a live :class:`~harness_core.agent.task_list.TaskList`.

Args:
    payload: The ``TaskListPayload`` snapshot to render.

Returns:
    A string containing the formatted task list ready for context injection.

## Signature
```python
render_task_list_markdown_from_payload(payload: TaskListPayload) -> str
```

## References
- [Module: harness_core.terminal_io.task_display](harness_core_terminal_io_task_display) - Parent module
