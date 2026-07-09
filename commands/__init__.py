"""Slash-command handlers (/exit, /quit, /sub, etc.)."""

from terminal_io.display import print_system
from commands.exit_quit import cmd_exit
from commands.save_session import cmd_save_session
from commands.load_session import cmd_load_session
from commands.new import cmd_new
from commands.compress import compress_handler

# For backward compatibility
_cmd_exit = cmd_exit


def cmd_sub(rest: str, agent=None) -> bool | None:
    """Spawn an interactive sub-agent conversation."""
    # Import here to avoid circular imports at module load time.
    from commands.sub import cmd_sub as _cmd_sub
    return _cmd_sub(rest, agent)


def cmd_tasks(rest: str, agent=None) -> bool | None:
    """Handle the /tasks command."""
    from commands.tasks import cmd_tasks as _cmd_tasks
    return _cmd_tasks(rest, agent)


# Command registry mapping command names to handler functions
COMMANDS = {
    'exit': cmd_exit,
    'quit': cmd_exit,  # Same function, different name in dict
    'sub': cmd_sub,
    'tasks': cmd_tasks,
    'save': cmd_save_session,
    'load': cmd_load_session,
    'new': cmd_new,
    'compress': compress_handler,
}