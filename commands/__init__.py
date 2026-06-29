"""Slash-command handlers (/exit, /quit, /sub)."""

from terminal_io.display import print_system


def cmd_exit(rest: str, agent=None) -> bool | None:
    """Handle the /exit command. Returns True to break the loop."""
    print_system("Goodbye!", "See you next time.")
    return True  # signal break


def cmd_quit(rest: str, agent=None) -> bool | None:
    """Handle the /quit command. Returns True to break the loop."""
    print_system("Goodbye!", "See you next time.")
    return True  # signal break


def cmd_sub(rest: str, agent=None) -> bool | None:
    """Spawn an interactive sub-agent conversation.

    Args:
        rest: The sub-agent name (e.g. ``"analyst"`` from ``/sub analyst``).
        agent: The calling parent agent. Used to inject the summary back into 
               its message history when the user exits the sub-agent.

    Returns:
        False to continue the parent loop after returning from the sub-agent,
        or True if an error occurs and we want to break (currently never).
    """
    # Import here to avoid circular imports at module load time.
    from commands.sub import cmd_sub as _cmd_sub
    return _cmd_sub(rest, agent)


COMMANDS = {
    'exit': cmd_exit,
    'quit': cmd_quit,
    'sub': cmd_sub,
}
