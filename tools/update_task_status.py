"""update_task_status — Tool for updating a task's execution state."""

from agent.task_list import get_task_list


def update_task_status(task_id: int, status: str) -> tuple:
    """Update the status of a specific task in the TaskList.
    
    This tool modifies the state of an existing task to reflect progress
    through the lifecycle (pending → in_progress → completed/failed).
    
    Args:
        task_id: The unique identifier of the task to update.
        status: The new status value. Must be one of: "pending", "in_progress", 
                "completed", or "failed".
    
    Returns:
        A (type, text) tuple indicating success or failure.
        
    Raises:
        ValueError: If the status is invalid or task_id doesn't exist.
    """
    try:
        task_list = get_task_list()
        updated = task_list.update_status(task_id, status)
        if updated:
            return ("task_list", f"Updated task {task_id} to '{status}'.")
        else:
            return ("_error_", f"Task ID {task_id} not found in the list.")
    except ValueError as e:
        return ("_error_", f"Failed to update task status: {e}")


function_def = {
    "type": "function",
    "function": {
        "name": "update_task_status",
        "description": (
            "Update the status of a specific task in the execution state machine. "
            "Valid statuses: 'pending', 'in_progress', 'completed', 'failed'. "
            "Use this to track progress through the task lifecycle."
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
