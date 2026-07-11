"""Handler for the /new command."""

from harness_core.terminal_io.display import print_system
from harness_core.session.session import Session


def cmd_new(rest: str, agent=None) -> bool | None:
    """Create a new session in the current agent.

    Resets both the task list and conversation history, keeping only the system prompt.
    A new session file is generated with a fresh timestamped filename.

    Usage:
        /new                 - create a brand-new session (resets everything)

    Args:
        rest: Unused (kept for consistency with other command handlers).
        agent: The current Agent instance.

    Returns:
        False to continue the loop after resetting.
    """
    if agent is None:
        print_system("Error", "No active session to reset.")
        return False

    # 1. Reset the task list (clear all tasks)
    if agent._task_list is not None:
        agent._task_list.reset()
    
    # 2. Create a brand new Session with only the system prompt and fresh session file.
    new_session = Session(
        system_prompt=agent._agent_type.system_prompt,
        task_list=agent._task_list,
        auto_save=True,
    )
    # Preserve the current agent type name for filename consistency.
    new_session._agent_type_name = agent._agent_type.name
    
    # 3. Replace the agent's session.
    agent._session = new_session
    
    print_system(
        "New Session Created",
        f"Starting fresh — conversation history cleared, task list reset."
    )
    return False