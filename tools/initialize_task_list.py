"""initialize_task_list — Tool for initializing the task execution state machine."""

from agent.core import CURRENT_AGENT
from tools.tool_result import ToolResult
from tools.utils import _strip_ansi


def initialize_task_list(tasks: list[str]) -> tuple | ToolResult:
    """Initialize or reset the task list with a new set of tasks.

    This tool clears any existing tasks and populates the current agent's TaskList instance
    with a fresh set of pending tasks based on the provided descriptions.

    Args:
        tasks: A list of strings, each representing a task description.
               Each string becomes one task with auto-incremented IDs.

    Returns:
        On success: a :class:`ToolResult` containing status text for the LLM and
            the full formatted task list for user display.
        On failure: a ``(type_tag, text)`` tuple indicating an error condition.

    Raises:
        ValueError: If the input is invalid (empty list, empty descriptions).
    """
    current_agent = CURRENT_AGENT.get()
    
    if not current_agent or not hasattr(current_agent, '_task_list'):
        return ToolResult(
            llm_text=_strip_ansi("No active agent context found"),
            display_text=_strip_ansi("No active agent context found"),
            type_tag="text",
            title="🚫 Error",
            theme="error",
        )

    try:
        current_agent._task_list.initialize_tasks(tasks)
        return ToolResult(
            llm_text=f"Initialized {len(tasks)} tasks successfully.",
            display_text=current_agent._task_list.to_markdown(),
            type_tag="markdown",
            title="📋 Task List",
            theme="status",
        )
    except ValueError as e:
        return ToolResult(
            llm_text=_strip_ansi(f"Failed to initialize task list: {e}"),
            display_text=_strip_ansi(f"Failed to initialize task list: {e}"),
            type_tag="text",
            title="🚫 Error",
            theme="error",
        )


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
