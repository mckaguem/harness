---
name: "harness_core.agent.task_list"
description: "TaskList — cache-friendly state machine for tracking agent execution."
source: "harness_core/agent/task_list.py"
---

TaskList — cache-friendly state machine for tracking agent execution.

This module provides a robust TaskList class that manages the lifecycle of
execution tasks within an LLM agent's context window. It is designed to be
cache-friendly by keeping all dynamic state in a structured format that can be
injected into message payloads without modifying the static system prompt.

Each Agent instance maintains its own TaskList for independent task tracking,
enabling multiple agents to operate concurrently without shared state conflicts.

## References
- [Task](harness_core_agent_task_list_Task) - Represents a single executable task within the agent's workflow
  - [__post_init__](harness_core_agent_task_list_Task___post_init__) - Validate that status is one of the allowed values
  - [to_json](harness_core_agent_task_list_Task_to_json) - Serialize this task to a JSON-compatible dictionary with explicit ID
- [NextTaskInfo](harness_core_agent_task_list_NextTaskInfo) - Information about the next uncompleted task, returned by update_status
- [TaskList](harness_core_agent_task_list_TaskList) - Manages a collection of tasks and their lifecycle states
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
- [VALID_STATUSES](harness_core_agent_task_list_VALID_STATUSES) - Constant
- [Module Index](../index/harness_core_agent.md) - Parent module index
