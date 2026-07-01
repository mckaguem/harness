"""initialize_task_list — Tool for initializing the task execution state machine."""

from agent.core import CURRENT_AGENT


def initialize_task_list(tasks: list[str]) -> tuple:
    """Initialize or reset the task list with a new set of tasks.

    This tool clears any existing tasks and populates the current agent's TaskList instance
    with a fresh set of pending tasks based on the provided descriptions.

    Args:
        tasks: A list of strings, each representing a task description.
               Each string becomes one task with auto-incremented IDs.

    Returns:
        A (type_tag, text) tuple indicating success or failure.
        type_tag is "text" on success or "_error_" on failure.

    Raises:
        ValueError: If the input is invalid (empty list, empty descriptions).
    """
    current_agent = CURRENT_AGENT.get()
    
    if not current_agent or not hasattr(current_agent, '_task_list'):
        return ("_error_", "No active agent context found")

    try:
        current_agent._task_list.initialize_tasks(tasks)
        return ("text", f"Initialized {len(tasks)} tasks successfully.")
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
