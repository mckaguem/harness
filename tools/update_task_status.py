"""update_task_status — Tool for updating task execution state machine."""

from agent.core import CURRENT_AGENT


def update_task_status(task_id: int, status: str) -> tuple:
    """Update the status of a specific task.

    Updates the status field of a Task object in the current agent's TaskList instance.
    The new status must be one of VALID_STATUSES (pending, in_progress, completed, failed).

    Args:
        task_id: Integer ID of the task to update
        status: New status value (must be one of VALID_STATUSES)

    Returns:
        A (type_tag, text) tuple indicating success or failure.
        type_tag is "text" on success or "_error_" on failure.

    Raises:
        ValueError: If the provided status is not in VALID_STATUSES.
    """
    current_agent = CURRENT_AGENT.get()

    if not current_agent or not hasattr(current_agent, '_task_list'):
        return ("_error_", "No active agent context found")

    try:
        updated = current_agent._task_list.update_status(task_id, status)
        if updated:
            return ("text", f"Task {task_id} updated to '{status}' successfully.")
        else:
            return ("_error_", f"Task with ID {task_id} not found in current task list")
    except ValueError as e:
        return ("_error_", str(e))


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
