"""Handler for the /tasks command — print the current task list."""

from agent.core import CURRENT_AGENT
from terminal_io.display import display_message_panel


def cmd_tasks(rest: str, agent=None) -> bool | None:
    """Handle the /tasks command. Displays all tasks and their statuses.

    Args:
        rest: Unused (kept for API consistency with other commands).
        agent: Optional pre-resolved Agent instance for testing. If ``None``,
               the active agent is read from :data:`CURRENT_AGENT`.

    Returns:
        False to continue the parent loop (this is a display-only command).
    """
    # Use CURRENT_AGENT context variable like update_task_status does
    if agent is not None:
        current_agent = agent
    else:
        current_agent = CURRENT_AGENT.get()
    
    if not current_agent:
        display_message_panel(
            "No active task list.",
            theme="error",
            title="📋 Tasks",
        )
        return False

    tasks = current_agent.task_list.tasks
    if not tasks:
        display_message_panel(
            "No tasks have been initialized yet.",
            theme="status",
            title="📋 Tasks",
        )
        return False

    display_message_panel(
        current_agent.task_list.to_markdown(),
        theme="status",
        title="📋 Tasks",
    )

    return False
