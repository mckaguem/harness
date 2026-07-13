"""Task display utilities for rendering TaskList as formatted Markdown.

This module separates the view layer (formatting) from the model (TaskList),
enabling cleaner separation of concerns and easier testing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness_core.event_types import TaskInfo, TaskListPayload

if TYPE_CHECKING:
    from harness_core.agent.task_list import TaskList


def render_task_list_markdown(task_list: "TaskList") -> str:
    """Render the current task list state as a formatted markdown string.

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
    """
    lines = ["### SYSTEM STATE: CURRENT TASK LIST"]

    for task in task_list.tasks:
        if task.status == "completed":
            marker = "[x]"
            line = f"- {marker} {task.description}"
        elif task.status == "in_progress":
            marker = "[*]"
            line = f"- {marker} {task.description} *(CURRENT)*"
        elif task.status == "failed":
            marker = "[!]"
            line = f"- {marker} {task.description} *(FAILED)*"
        else:  # pending
            marker = "[ ]"
            line = f"- {marker} {task.description}"

        lines.append(line)

    return "\n".join(lines)


def render_task_list_markdown_from_payload(payload: TaskListPayload) -> str:
    """Render a :class:`TaskListPayload` (event payload) as markdown.

    Produces the same checkbox-list markdown as :func:`render_task_list_markdown`
    but sourced from the serializable ``TaskInfo`` list carried by the event
    payload rather than a live :class:`~harness_core.agent.task_list.TaskList`.

    Args:
        payload: The ``TaskListPayload`` snapshot to render.

    Returns:
        A string containing the formatted task list ready for context injection.
    """
    lines = ["### SYSTEM STATE: CURRENT TASK LIST"]

    for task in payload.tasks:
        if task.status == "completed":
            marker = "[x]"
            line = f"- {marker} {task.description}"
        elif task.status == "in_progress":
            marker = "[*]"
            line = f"- {marker} {task.description} *(CURRENT)*"
        elif task.status == "failed":
            marker = "[!]"
            line = f"- {marker} {task.description} *(FAILED)*"
        else:  # pending
            marker = "[ ]"
            line = f"- {marker} {task.description}"

        lines.append(line)

    return "\n".join(lines)