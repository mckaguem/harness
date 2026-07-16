"""Terminal I/O layer — Rich-based rendering via the Textual TUI."""


# ── Public surface (re-exported from submodules) ───────────────────────

from .speed import format_speed, format_tool_elapsed
from .prompt import prompt_user
from .display import (
    print_system,
    display_tool_call,
    display_tool_result,
    display_error,
    display_agent_response,
    display_user_message,
    display_turn_stats,
    reset_pending_tool_panel,
)

# The textual TUI app + controller live in the ``tui`` submodule and are
# imported by callers that want to launch the full-screen interface.
from . import tui  # noqa: F401  (exposes terminal_io.tui.launch / get_tui)


__all__ = [
    "format_speed",
    "format_tool_elapsed",
    "display_agent_response",
    "display_user_message",
    "display_turn_stats",
    "display_error",
    "display_tool_call",
    "display_tool_result",
    "reset_pending_tool_panel",
    "print_system",
    "prompt_user",
    "tui",
]
