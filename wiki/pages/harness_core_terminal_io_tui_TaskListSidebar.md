---
name: "harness_core.terminal_io.tui.TaskListSidebar"
description: "A right-hand panel that renders the main agent's task list."
source: "harness_core/terminal_io/tui.py"
---

A right-hand panel that renders the main agent's task list.

Its content is refreshed from the agent's :class:`~harness_core.agent.task_list.TaskList`
via :meth:`refresh_tasks`, which is normally driven by a change listener on the
TaskList so it stays in sync with every ``initialize_task_list`` / ``update_task_status``
tool call.  A periodic interval keeps it correct even if the listener is missed.

## Methods
- **__init__(self, *args, **kwargs) -> None** - No description
- **set_agent(self, agent) -> None** - Provide the agent whose task list should be displayed
- **set_usage(self, text: str | None) -> None** - Store the most recent LLM usage summary to render above the tasks
- **refresh_tasks(self) -> None** - Re-render the sidebar
- **refresh_tasks_from_payload(self, payload: TaskListPayload) -> None** - Re-render the task list from a TaskListPayload (event-driven)

## Class Variables
None

## References
- [Module: harness_core.terminal_io.tui](harness_core_terminal_io_tui) - Parent module
- Base class: `Static`
- [__init__](harness_core_terminal_io_tui_TaskListSidebar___init__) - Method
- [set_agent](harness_core_terminal_io_tui_TaskListSidebar_set_agent) - Provide the agent whose task list should be displayed
- [set_usage](harness_core_terminal_io_tui_TaskListSidebar_set_usage) - Store the most recent LLM usage summary to render above the tasks
- [refresh_tasks](harness_core_terminal_io_tui_TaskListSidebar_refresh_tasks) - Re-render the sidebar
- [refresh_tasks_from_payload](harness_core_terminal_io_tui_TaskListSidebar_refresh_tasks_from_payload) - Re-render the task list from a TaskListPayload (event-driven)
