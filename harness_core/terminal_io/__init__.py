"""Terminal I/O layer — Rich-based rendering with an optional textual TUI."""


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
)

# The textual TUI app + controller live in the ``tui`` submodule and are
# imported lazily by callers that want to launch the full-screen interface.
from . import tui  # noqa: F401  (exposes terminal_io.tui.launch / get_tui)


__all__ = [
    "format_speed",
    "format_tool_elapsed",
    "display_agent_response",
    "display_user_message",
    "display_error",
    "display_tool_call",
    "display_tool_result",
    "print_system",
    "prompt_user",
    "tui",
]
