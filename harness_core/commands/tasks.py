"""Handler for the /tasks command — print the current task list."""

from harness_core.terminal_io.display import display_message_panel
from harness_core.terminal_io.task_display import render_task_list_markdown


def cmd_tasks(rest: str, agent=None) -> bool | None:
    """Handle the /tasks command. Displays all tasks and their statuses.

    Args:
        rest: Unused (kept for API consistency with other commands).
        agent: Optional pre-resolved Agent instance. If ``None``, a friendly
               message is displayed instead of reading from context state.

    Returns:
        False to continue the parent loop (this is a display-only command).
    """
    if not agent:
        display_message_panel(
            "No active task list.",
            theme="error",
            title="📋 Tasks",
        )
        return False

    tasks = agent.task_list.tasks
    if not tasks:
        display_message_panel(
            "No tasks have been initialized yet.",
            theme="status",
            title="📋 Tasks",
        )
        return False

    display_message_panel(
        render_task_list_markdown(agent.task_list),
        theme="status",
        title="📋 Tasks",
    )

    return False
