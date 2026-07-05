"""update_task_status — Tool for updating task execution state machine."""

from agent.core import CURRENT_AGENT
from tools.tool_result import ToolResult
from tools.utils import _strip_ansi


def update_task_status(task_id: int, status: str) -> tuple | ToolResult:
    """Update the status of a specific task.

    Updates the status field of a Task object in the current agent's TaskList instance.
    The new status must be one of VALID_STATUSES (pending, in_progress, completed, failed).

    Args:
        task_id: Integer ID of the task to update
        status: New status value (must be one of VALID_STATUSES)

    Returns:
        On success: a :class:`ToolResult` containing status text for the LLM and
            the full formatted task list for user display.
        On failure: a ``(type_tag, text)`` tuple indicating an error condition.

    Raises:
        ValueError: If the provided status is not in VALID_STATUSES.
    """
    current_agent = CURRENT_AGENT.get()

    if not current_agent:
        return ToolResult(
            llm_text=_strip_ansi("No active agent context found"),
            display_text=_strip_ansi("No active agent context found"),
            type_tag="text",
            title="🚫 Error",
            theme="error",
        )

    try:
        updated = current_agent.task_list.update_status(task_id, status)
        if updated:
            return ToolResult(
                llm_text=f"Task {task_id} updated to '{status}' successfully.",
                display_text=current_agent.task_list.to_markdown(),
                type_tag="markdown",
                title="📋 Task List",
                theme="status",
            )
        else:
            return ToolResult(
                llm_text=_strip_ansi(f"Task with ID {task_id} not found in current task list"),
                display_text=_strip_ansi(f"Task with ID {task_id} not found in current task list"),
                type_tag="text",
                title="🚫 Error",
                theme="error",
            )
    except ValueError as e:
        return ToolResult(
            llm_text=_strip_ansi(str(e)),
            display_text=_strip_ansi(str(e)),
            type_tag="text",
            title="🚫 Error",
            theme="error",
        )


function_def = {
    "type": "function",
    "function": {
        "name": "update_task_status",
        "description": (
            "Update the status of a specific task in the execution state machine. "
            "Valid statuses: 'pending', 'in_progress', 'completed', 'failed'."
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
