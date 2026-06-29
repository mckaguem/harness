"""Slash-command handlers (/exit, /quit)."""

from terminal_io.display import print_system


def cmd_exit(rest: str) -> bool | None:
    """Handle the /exit command. Returns True to break the loop."""
    print_system("Goodbye!", "See you next time.")
    return True  # signal break


def cmd_quit(rest: str) -> bool | None:
    """Handle the /quit command. Returns True to break the loop."""
    print_system("Goodbye!", "See you next time.")
    return True  # signal break


COMMANDS = {
    'exit': cmd_exit,
    'quit': cmd_quit,
}
