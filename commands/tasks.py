"""Handler for the /tasks command — print the current task list."""

from agent.core import CURRENT_AGENT
from terminal_io.display import display_message_panel


def cmd_tasks(rest: str, agent=None) -> bool | None:
    """Handle the /tasks command. Displays all tasks and their statuses.

    Args:
        rest: Unused (kept for API consistency with other commands).
        agent: The calling agent whose ``_task_list`` holds the current TaskList.

    Returns:
        False to continue the parent loop (this is a display-only command).
    """
    # Use CURRENT_AGENT context variable like update_task_status does
    current_agent = CURRENT_AGENT.get()
    
    if not current_agent or not hasattr(current_agent, '_task_list'):
        display_message_panel(
            "No active task list.",
            theme="error",
            title="📋 Tasks",
        )
        return False

    tasks = getattr(current_agent._task_list, 'tasks', [])
    if not tasks:
        display_message_panel(
            "No tasks have been initialized yet.\nUse /initialize_task_list to add some.",
            theme="status",
            title="📋 Tasks",
        )
        return False

    lines = []
    for task in tasks:
        status = task.status.upper()
        lines.append(f"Task {task.id}) {task.description}   [{status}]")

    display_message_panel(
        "\n".join(lines),
        theme="status",
        title="📋 Tasks",
    )

    return False
