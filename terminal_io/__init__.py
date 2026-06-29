"""Terminal I/O layer — ANSI colours, boxes, markdown rendering, and display helpers.

This package re-exports the public API so existing imports like
``from terminal_io import print_box, prompt_user`` keep working unchanged.
"""


# ── Public surface (re-exported from submodules) ───────────────────────

# Colors & box drawing
from .colors import (
    RESET, BOLD, DIM,
    CYAN, GREEN, BLUE, YELLOW, RED, MAGENTA,
    BG_YELLOW, BG_RED,
    c,
)
from .boxes import print_box, STYLES, _safe_len

# Markdown rendering
from .markdown import (
    display_agent_response,
    _render_table, _render_code_block, _md_inline,
)
from .markdown.inline import _MD_INLINES

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
    display_tool_success,
    display_error,
)
from .trunc import _trunc_for_display, MAX_DISPLAY_LINES


__all__ = [
    # Colors
    "RESET", "BOLD", "DIM",
    "CYAN", "GREEN", "BLUE", "YELLOW", "RED", "MAGENTA",
    "BG_YELLOW", "BG_RED", "c",
    # Boxes
    "print_box", "STYLES", "_safe_len",
    # Markdown
    "display_agent_response",
    "_render_table", "_render_code_block", "_md_inline",
    "_MD_INLINES",
    # Speed
    "_format_speed",
    # Prompt
    "prompt_user",
    # Display helpers
    "print_system",
    "display_user_prompt",
    "display_tool_call",
    "display_tool_result",
    "display_tool_success",
    "display_error",
    # Truncation
    "_trunc_for_display",
    "MAX_DISPLAY_LINES",
]

__all__.sort()  # keep sorted for easy scanning
