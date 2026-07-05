"""Tool executor — handles dispatch, result formatting, and error wrapping."""

from tools.tool_result import ToolResult


class ToolExecutor:
    """Handles tool dispatching and result formatting for an agent.

    Encapsulates the mechanics of calling tools via the dispatcher registry
    and wrapping results (success or failure) in :class:`ToolResult` objects.
    This keeps tool execution concerns separate from conversation orchestration.
    """

    def __init__(self, agent_name: str = ""):
        self._agent_name = agent_name

    def execute(self, func_name: str, args: dict):
        """Dispatch a tool call by name and return its result (ToolResult or raise).

        Calls the registered tool function via :func:`tools.dispatcher.dispatch`.

        Args:
            func_name: The tool function name (e.g. ``"execute_bash"``).
            args: Keyword arguments to pass to the tool function.

        Returns:
            A :class:`ToolResult` from the successful tool execution.

        Raises:
            KeyError: If *func_name* is not registered in the dispatcher.
            Exception: Re-raised if the tool raises an unexpected error — callers
                       should catch this and wrap it in a ``ToolResult`` of their own.
        """
        from tools.dispatcher import dispatch
        return dispatch(func_name, args)

    def make_error_result(self, func_name: str, description: str) -> ToolResult:
        """Build a failure :class:`ToolResult` for a given error message.

        Args:
            func_name: The tool name that failed (used in the panel title).
            description: Human-readable error message to include as both LLM and display text.

        Returns:
            A ``ToolResult`` with ``theme="error"`` carrying the error details.
        """
        return ToolResult(
            llm_text=description,
            display_text=description,
            type_tag="text",
            title=f"Error: {func_name}",
            theme="error",
        )

    def make_submit_results_block(self, has_incomplete_tasks: bool) -> dict | None:
        """Return a blocking message payload if submit_results should be denied.

        When there are incomplete tasks (pending or in_progress), returns a
        dictionary containing the blocked message content and a corresponding
        ``ToolResult`` so callers can inject the block into the conversation
        without duplicating formatting logic.

        Args:
            has_incomplete_tasks: Whether :meth:`TaskList.has_incomplete_tasks` returned True.

        Returns:
            A dict ``{"role": "user", "content": "...", "result": ToolResult(...)}`` if blocking,
            or ``None`` if submit_results should proceed normally (no incomplete tasks).
        """
        if not has_incomplete_tasks:
            return None

        content = (
            "[SYSTEM ERROR] Execution termination blocked. "
            "You still have incomplete tasks in your state machine. "
            "You must finish them or update their status to 'failed' "
            "before you can invoke submit_results."
        )
        result = ToolResult(
            llm_text=content,
            display_text=content,
            type_tag="text",
            title=f"Error: submit_results",
            theme="error",
        )
        return {
            "role": "user",
            "content": content,
            "result": result,
        }
