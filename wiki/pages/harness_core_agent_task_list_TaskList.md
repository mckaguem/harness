---
name: "harness_core.agent.task_list.TaskList"
description: "Manages a collection of tasks and their lifecycle states."
source: "harness_core/agent/task_list.py"
---

Manages a collection of tasks and their lifecycle states.

This class provides methods to initialize, update, and query the state
of multiple tasks. It's designed for concurrent agent environments where
each Agent instance holds its own independent TaskList.

## Methods
- **__init__(self, id: str | None, sender_id: str | None)** - Initialize an empty TaskList instance
- **_emit(self, topic: str) -> None** - Publish a tasklist event if an event loop is running
- **initialize_tasks(self, tasks: list[str]) -> None** - Clear existing tasks and populate with a new list
- **reset(self) -> None** - Clear all tasks from the list
- **update_status(self, task_id: int, status: str) -> tuple[bool, NextTaskInfo]** - Update the status of a specific task
- **_build_next_task_info(self) -> NextTaskInfo** - Build a NextTaskInfo describing the current state of remaining work
- **has_incomplete_tasks(self) -> bool** - Check if there are any tasks that haven't been completed or failed
- **all_complete(self) -> bool** - Return True if every task is completed or failed (no pending/in_progress remain)
- **next_uncompleted_task(self) -> Task | None** - Return the first task that is still pending or in_progress, or None
- **to_json_list(self) -> list[dict]** - Render the full task list as a list of JSON-compatible dicts with explicit IDs
- **to_markdown(self) -> str** - Render the current task list state as a formatted markdown string

## Class Variables
None

## References
- [Module: harness_core.agent.task_list](harness_core_agent_task_list) - Parent module
- [__init__](harness_core_agent_task_list_TaskList___init__) - Initialize an empty TaskList instance
- [_emit](harness_core_agent_task_list_TaskList__emit) - Publish a tasklist event if an event loop is running
- [initialize_tasks](harness_core_agent_task_list_TaskList_initialize_tasks) - Clear existing tasks and populate with a new list
- [reset](harness_core_agent_task_list_TaskList_reset) - Clear all tasks from the list
- [update_status](harness_core_agent_task_list_TaskList_update_status) - Update the status of a specific task
- [_build_next_task_info](harness_core_agent_task_list_TaskList__build_next_task_info) - Build a NextTaskInfo describing the current state of remaining work
- [has_incomplete_tasks](harness_core_agent_task_list_TaskList_has_incomplete_tasks) - Check if there are any tasks that haven't been completed or failed
- [all_complete](harness_core_agent_task_list_TaskList_all_complete) - Return True if every task is completed or failed (no pending/in_progress remain)
- [next_uncompleted_task](harness_core_agent_task_list_TaskList_next_uncompleted_task) - Return the first task that is still pending or in_progress, or None
- [to_json_list](harness_core_agent_task_list_TaskList_to_json_list) - Render the full task list as a list of JSON-compatible dicts with explicit IDs
- [to_markdown](harness_core_agent_task_list_TaskList_to_markdown) - Render the current task list state as a formatted markdown string
