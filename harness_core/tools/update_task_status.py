"""update_task_status — Tool for updating task execution state machine."""

from typing import Any

from harness_core.agent.task_list import VALID_STATUSES
from harness_core.terminal_io.task_display import render_task_list_markdown
from harness_core.tools.tool_result import ToolResult
from harness_core.tools.utils import _strip_ansi, make_error_result


def update_task_status(agent: Any, task_id: int, status: str) -> ToolResult:
    """Update the status of a specific task.

    Updates the status field of a Task object in the current agent's TaskList instance.
    The new status must be one of VALID_STATUSES (pending, in_progress, completed, failed).

    On success this also returns structured info about what tasks remain:
      - ``next_task_id``: 1-indexed ID of the next pending/in_progress task to work on,
        or None if every task is done.
      - ``all_complete``: True when every task has been completed or failed.

    When ``all_complete`` is True, the agent's TaskList is reset so future injections
    stop including stale state and a message indicating completion is returned.

    Args:
        agent: The calling Agent instance (injected automatically by the dispatcher).
        task_id: Integer ID of the task to update (1-indexed).
        status: New status value (must be one of VALID_STATUSES).

    Returns:
        On success: a :class:`ToolResult` containing status text for the LLM and
            JSON-encoded remaining-task information for machine consumption.
        On failure: a :class:`ToolResult` error (produced by :func:`make_error_result`).

    Raises:
        ValueError: If the provided status is not in VALID_STATUSES.
    """
    try:
        success, next_info = agent.task_list.update_status(task_id, status)

        # If all tasks are now done, clear the task list so injection stops.
        if next_info.all_complete:
            agent.task_list.reset()
            return ToolResult(
                llm_text=(
                    f"Task {task_id} updated to '{status}'. "
                    f"All tasks complete. Task list cleared."
                ),
                display_text=(
                    f"### ✅ All Tasks Complete\n\n"
                    f"- Task **{task_id}** → `{status}`\n"
                    f"\nTask list has been reset. No further task injections will appear in your context."
                ),
                type_tag="markdown",
                title="✅ Task List Complete",
                theme="status",
            )

        # Build machine-friendly payload with the next ID to act on.
        remaining_json = _strip_ansi(str(agent.task_list.to_json_list()))
        llm_text_parts = [
            f"Task {task_id} updated to '{status}' successfully.",
        ]
        if next_info.has_next:
            llm_text_parts.append(
                f"Next task: ID={next_info.id}, description='{next_info.description}', "
                f"status='{next_info.status}'."
            )

        return ToolResult(
            llm_text="\n".join(llm_text_parts),
            display_text=render_task_list_markdown(agent.task_list),
            type_tag="markdown",
            title="📋 Task List",
            theme="status",
        )
    except ValueError as e:
        return make_error_result(str(e))


def summary(task_id: int, status: str) -> str:
    """Return a one-line summary string for the update_task_status action.

    Args:
        task_id: Integer ID of the task to update (1-indexed).
        status: New status value.

    Returns:
        A one-line summary string in the format:
        "update task status: task {task_id} set to '{status}'"
    """
    return f"update task status: task {task_id} set to '{status}'"


function_def = {
    "type": "function",
    "function": {
        "name": "update_task_status",
        "description": (
            "Update the status of a specific task in the execution state machine. "
            "Valid statuses: 'pending', 'in_progress', 'completed', 'failed'.\n"
            "Task IDs are 1-indexed (first task is ID=1). "
            "When all tasks become completed/failed, the task list will be cleared automatically."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "The unique identifier of the task to update."
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "failed"],
                    "description": "The new status value for the task."
                }
            },
            "required": ["task_id", "status"]
        }
    }
}
