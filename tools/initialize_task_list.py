"""initialize_task_list — Tool for initializing the task execution state machine."""

from agent.context import CURRENT_AGENT
from agent.tool_context import ToolContext
from tools.tool_result import ToolResult
from tools.utils import _strip_ansi, make_error_result


def initialize_task_list(tasks: list[str], ctx: ToolContext | None = None) -> tuple | ToolResult:
    """Initialize or reset the task list with a new set of tasks.

    This tool clears any existing tasks and populates the current agent's TaskList instance
    with a fresh set of pending tasks based on the provided descriptions.

    Returns an error if there are currently incomplete (pending/in_progress) tasks. The caller
    should either complete all tasks first or wait for them to be auto-cleared by update_task_status.

    Args:
        tasks: A list of strings, each representing a task description.
               Each string becomes one task with auto-incremented IDs starting from 1.

    Returns:
        On success: a :class:`ToolResult` containing status text for the LLM and
            JSON-encoded task list for machine consumption.
        On failure: a ``(type_tag, text)`` tuple indicating an error condition.

    Raises:
        ValueError: If the input is invalid (empty list, empty descriptions),
                    or if there are incomplete tasks remaining in the current list.
    """
    current_agent = getattr(ctx, "agent", None) if ctx is not None else None
    if current_agent is None:
        current_agent = CURRENT_AGENT.get()
    if current_agent is None:
        return make_error_result(
            "No active agent context found. The task list tool can only be used "
            "by an agent running inside a handle_prompt loop (or a sub-agent loop)."
        )

    try:
        current_agent.task_list.initialize_tasks(tasks)
        json_repr = str(current_agent.task_list.to_json_list())
        return ToolResult(
            llm_text=(
                f"Initialized {len(tasks)} tasks successfully. "
                f"Task IDs start at 1. JSON: `{json_repr}`"
            ),
            display_text=(
                f"### 📋 Task List Initialized\n\n"
                f"{len(tasks)} task(s) created:\n\n"
                + current_agent.task_list.to_markdown()
            ),
            type_tag="markdown",
            title="📋 Task List",
            theme="status",
        )
    except ValueError as e:
        return make_error_result(str(e))


function_def = {
    "type": "function",
    "function": {
        "name": "initialize_task_list",
        "description": (
            "Initialize a new task execution state machine. Each input string becomes one task "
            "with auto-incremented IDs starting from 1.\n"
            "ERROR: Returns an error if there are currently incomplete (pending/in_progress) tasks "
            "in the existing list — complete or fail all tasks first, then call this tool again."
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
