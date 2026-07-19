"""goal_met — Tool for clearing the agent's current goal once all tasks are complete."""

from typing import Any

from harness_core.tools.tool_result import ToolResult
from harness_core.tools.utils import make_error_result


def goal_met(agent: Any, ) -> ToolResult:
    """Clear the current goal now that all tasks are complete.

    This tool clears the agent's ``goal`` (``self.goal``) once the task list has
    no remaining incomplete tasks. It is intended to be called at the end of a
    workflow to signal that the objective has been met and the turn may end.

    If there are still incomplete (pending/in_progress) tasks in the task list,
    the tool returns an error instructing the caller to resolve them first.

    Args:
        agent: The calling Agent instance (injected automatically by the dispatcher).

    Returns:
        On success: a :class:`ToolResult` confirming the goal was cleared.
        On failure: a :class:`ToolResult` error (produced by :func:`make_error_result`).
    """
    if agent is None:
        return make_error_result("No agent context available.")

    if agent.task_list.has_incomplete_tasks():
        return make_error_result(
            "Cannot clear the goal: you still have incomplete tasks in your task list. "
            "Call update_task_status to mark each task as 'completed' or 'failed' before calling goal_met."
        )

    agent.goal = ""
    return ToolResult(
        llm_text="Goal cleared. You may now end your turn.",
        display_text=(
            "### ✅ Goal Cleared\n\n"
            "The current goal has been cleared. You may now end your turn."
        ),
        type_tag="markdown",
        title="✅ Goal Met",
        theme="status",
    )


def summary() -> str:
    """Return a one-line summary of the goal_met call."""
    return "goal_met: clear the current goal"


function_def = {
    "type": "function",
    "function": {
        "name": "goal_met",
        "description": (
            "Clear the agent's current goal (self.goal) once all work is done. "
            "This should be called at the end of a workflow to signal the objective has been met "
            "and the turn may end.\n"
            "ERROR: Returns an error if the task list still has incomplete (pending/in_progress) tasks — "
            "call update_task_status to mark each task as 'completed' or 'failed' before calling goal_met."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}
