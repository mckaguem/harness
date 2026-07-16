---
name: "harness_core.agent.task_list.to_markdown"
description: "Render the current task list state as a formatted markdown string."
source: "harness_core/agent/task_list.py"
---

Render the current task list state as a formatted markdown string.

Deprecated: prefer the view function
:func:`harness_core.terminal_io.task_display.render_task_list_markdown`,
which keeps markdown rendering (the View) separate from this model. This
method is retained only because the test suite still exercises it.

The output is designed to be injected directly into LLM message payloads
with clear visual delimiters and status indicators using checkbox syntax:
- [x] for completed tasks (checkmark)
- [*] for in-progress tasks (with CURRENT marker)
- [ ] for pending tasks (empty checkbox)
- [!] for failed tasks (exclamation mark, italic FAILED label)

Returns:
    A string containing the formatted task list ready for context injection.

## Signature
```python
to_markdown(self) -> str
```

## References
- [Module: harness_core.agent.task_list](harness_core_agent_task_list) - Parent module
- [Class: TaskList](harness_core_agent_task_list_TaskList) - Parent class
