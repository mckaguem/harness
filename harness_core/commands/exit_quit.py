"""Handler for the /exit and /quit commands."""

from harness_core.terminal_io.display import print_system


def cmd_exit(_rest, agent=None) -> bool:
    """Handle the /exit and /quit commands. Returns True to break the loop."""
    print_system("Goodbye!", "See you next time.")
    return True  # signal break