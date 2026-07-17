"""initialize_task_list — Tool for initializing the task execution state machine."""

from typing import Any

from harness_core.terminal_io.task_display import render_task_list_markdown
from harness_core.tools.tool_result import ToolResult
from harness_core.tools.utils import make_error_result


def initialize_task_list(agent: Any, tasks: list[str]) -> ToolResult:
    """Initialize or reset the task list with a new set of tasks.

    This tool clears any existing tasks and populates the current agent's TaskList instance
    with a fresh set of pending tasks based on the provided descriptions.

    Returns an error if there are currently incomplete (pending/in_progress) tasks. The caller
    should either complete all tasks first or wait for them to be auto-cleared by update_task_status.

    Args:
        agent: The calling Agent instance (injected automatically by the dispatcher).
        tasks: A list of strings, each representing a task description.
               Each string becomes one task with auto-incremented IDs starting from 1.

    Returns:
        On success: a :class:`ToolResult` containing status text for the LLM and
            JSON-encoded task list for machine consumption.
        On failure: a :class:`ToolResult` error (produced by :func:`make_error_result`).

    Raises:
        ValueError: If the input is invalid (empty list, empty descriptions),
                    or if there are incomplete tasks remaining in the current list.
    """
    if agent is None:
        return make_error_result("No agent context available.")

    try:
        agent.task_list.initialize_tasks(tasks)
        json_repr = str(agent.task_list.to_json_list())
        return ToolResult(
            llm_text=(
                f"Initialized {len(tasks)} tasks successfully. "
                f"Task IDs start at 1. JSON: `{json_repr}`"
            ),
            display_text=(
                f"### 📋 Task List Initialized\n\n"
                f"{len(tasks)} task(s) created:\n\n"
                + render_task_list_markdown(agent.task_list)
            ),
            type_tag="markdown",
            title="📋 Task List",
            theme="status",
        )
    except ValueError as e:
        return make_error_result(str(e))


def summary(tasks: list[str]) -> str:
    """Return a one-line summary of the initialize_task_list call."""
    return f"initialize_task_list: {len(tasks)} task(s)"


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
