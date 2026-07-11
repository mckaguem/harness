"""Handler for the /save command."""

from harness_core.terminal_io.display import print_system


def cmd_save_session(rest: str, agent=None) -> bool | None:
    """Save the current session to a YAML file in .sessions/.

    Usage:
        /save                    - auto-generated filename with timestamp + agent type
        /save my_custom_name     - uses 'my_custom_name.yaml' as filename

    Args:
        rest: Optional custom filename (without extension).
        agent: The current Agent instance.

    Returns:
        False to continue the loop after saving.
    """
    if agent is None:
        print_system("Error", "No active session to save.")
        return False

    # Determine filename from optional user input
    custom_name = rest.strip() if rest and rest.strip() else None
    if custom_name:
        # If user provides a name with .yaml extension, strip it; otherwise append it.
        if not custom_name.endswith(".yaml"):
            custom_name += ".yaml"
        filename = custom_name
    else:
        filename = None  # auto-generate via timestamp + agent type

    session = agent._session
    success, message = session.export_session(
        filename=filename,
        agent_type_name=agent._agent_type.name,
    )

    if success:
        print_system("Session Saved", f"Saved to: {message}")
    else:
        print_system("Save Failed", message)

    return False