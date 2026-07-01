"""Terminal I/O layer — Rich-based rendering for display and tools."""


# ── Public surface (re-exported from submodules) ───────────────────────

from .speed import _format_speed
from .prompt import prompt_user
from .display import (
    print_system,
    display_tool_call,
    display_tool_result,
    display_error,
    display_agent_response,
)


__all__ = [
    "_format_speed",
    "display_agent_response",
    "display_error",
    "display_tool_call",
    "display_tool_result",
    "print_system",
    "prompt_user",
]
