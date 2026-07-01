"""initialize_task_list — Tool for initializing the task execution state machine."""

from agent.task_list import get_task_list


def initialize_task_list(tasks: list[str]) -> tuple:
    """Initialize or reset the task list with a new set of tasks.
    
    This tool clears any existing tasks and populates the TaskList singleton
    with a fresh set of pending tasks based on the provided descriptions.
    
    Args:
        tasks: A list of strings, each representing a task description.
               Each string becomes one task with auto-incremented IDs.
    
    Returns:
        A (type, text) tuple indicating success or failure.
        
    Raises:
        ValueError: If the input is invalid (empty list, empty descriptions).
    """
    try:
        task_list = get_task_list()
        task_list.initialize_tasks(tasks)
        return ("task_list", f"Initialized {len(tasks)} tasks successfully.")
    except ValueError as e:
        return ("_error_", f"Failed to initialize task list: {e}")


function_def = {
    "type": "function",
    "function": {
        "name": "initialize_task_list",
        "description": (
            "Initialize or reset the task execution state machine. "
            "Clears any existing tasks and creates a new list of pending tasks. "
            "Each input string becomes one task with auto-incremented IDs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of task descriptions to initialize. Each string becomes one task."
                }
            },
            "required": ["tasks"]
        }
    }
}
