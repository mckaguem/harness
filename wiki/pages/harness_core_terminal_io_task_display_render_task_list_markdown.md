---
name: "harness_core.terminal_io.task_display.render_task_list_markdown"
description: "Render the current task list state as a formatted markdown string."
source: "harness_core/terminal_io/task_display.py"
---

Render the current task list state as a formatted markdown string.

The output is designed to be injected directly into LLM message payloads
with clear visual delimiters and status indicators using checkbox syntax:
- [x] for completed tasks (checkmark)
- [*] for in-progress tasks (with CURRENT marker)
- [ ] for pending tasks (empty checkbox)
- [!] for failed tasks (exclamation mark, italic FAILED label)

Args:
    task_list: The TaskList instance to render.

Returns:
    A string containing the formatted task list ready for context injection.

## Signature
```python
render_task_list_markdown(task_list: 'TaskList') -> str
```

## References
- [Module: harness_core.terminal_io.task_display](harness_core_terminal_io_task_display) - Parent module
