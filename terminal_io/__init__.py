"""Terminal I/O layer — Rich-based rendering for display, markdown, and tools."""


# ── Public surface (re-exported from submodules) ───────────────────────

# Colors (re-exported for tools)
from .colors import c, RESET, BOLD, DIM, CYAN, GREEN, BLUE, YELLOW, RED, MAGENTA

# Speed formatting
from .speed import _format_speed

# User input
from .prompt import prompt_user

# Display helpers
from .display import (
    print_system,
    display_user_prompt,
    display_tool_call,
    display_tool_result,
    display_tool_call_with_result,
    display_tool_success,
    display_error,
    display_agent_response,
)

# Truncation
from .trunc import _trunc_for_display, MAX_DISPLAY_LINES


__all__ = [
    # Colors (re-exported for tools)
    "BOLD",
    "BLUE",
    "CYAN",
    "c",
    "DIM",
    "GREEN",
    "MAGENTA",
    "RED",
    "RESET",
    "YELLOW",
    # Display helpers
    "display_agent_response",
    "display_error",
    "display_tool_call",
    "display_tool_call_with_result",
    "display_tool_result",
    "display_tool_success",
    "display_user_prompt",
    "print_system",
    # Prompt
    "prompt_user",
    # Speed
    "_format_speed",
    # Truncation
    "_trunc_for_display",
    "MAX_DISPLAY_LINES",
]

__all__.sort()  # keep sorted for easy scanning
