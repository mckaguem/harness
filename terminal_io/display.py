"""High-level display helpers — thin wrappers that coordinate boxes, markdown, etc."""

from __future__ import annotations

import os
import re

from .colors import c, GREEN, RED, BOLD, DIM, CYAN, YELLOW, RESET
from .boxes import print_box, STYLES, _safe_len
from .trunc import _trunc_for_display


def _wrap_text(text: str, max_width: int) -> list[str]:
    """Wrap text to fit within *max_width* columns, preserving ANSI escapes."""
    lines = []
    for raw_line in text.splitlines():
        # Split on ANSI codes so we can measure visible length correctly.
        segments = re.split(r'(\033\[[^m]*m)', raw_line)
        current = ""
        current_len = 0
        for seg in segments:
            if seg.startswith('\033'):
                current += seg
            else:
                visible = len(seg)
                if current_len + visible <= max_width:
                    current += seg
                    current_len += visible
                else:
                    # Try to break at a space.
                    remaining = max_width - current_len
                    last_space = seg.rfind(' ', 0, remaining)
                    if last_space > 0:
                        lines.append(current + seg[:last_space])
                        seg = seg[last_space+1:]
                        current = ""
                        current_len = 0
                    # Force break the rest.
                    while len(seg) > max_width:
                        lines.append(current + seg[:max_width])
                        seg = seg[max_width:]
                        current = ""
                        current_len = 0
                    if seg:
                        current += seg
                        current_len += len(seg)
        if current:
            lines.append(current)
    return lines


def print_system(title: str, message: str) -> None:
    """Print a system-level notification box."""
    print_box(title, message, style="system")


def display_user_prompt(user_input: str) -> None:
    """Print a box showing what the user typed (with char count)."""
    print_box(f"📝 Your Prompt ({len(user_input)} chars)", user_input, style="user")


def display_tool_call(func_name: str, args_str: str) -> None:
    """Print a tool-call box showing the function name and its arguments."""
    print_box(f"🔧 {func_name}", args_str, style="tool_call")


def display_tool_result(func_name: str, result: str) -> None:
    """Print a truncated tool-result box (full result is kept separately)."""
    display_result = _trunc_for_display(str(result))
    print_box(f"✅ {func_name} Result", display_result, style="tool_result")


def display_tool_call_with_result(func_name: str, args_str: str, result: str) -> None:
    """Print a single combined box containing the tool call and its result,
    separated by a divider line.
    """

    # Resolve terminal width (mirror the logic inside print_box so we don't
    # have to render twice).
    style = STYLES["tool_call"]
    colour = style["colour"]
    border_char = style["border"]  # e.g. "+-+"
    try:
        width = os.get_terminal_size().columns
    except (OSError, AttributeError):
        width = 80

    border_top = "+" + "-" * (width - 2) + "+"
    border_bot = "+" + "-" * (width - 2) + "+"
    sep_border = "+" + "─" * (width - 2) + "+"

    # ── Title bar (reuses existing print_box convention)
    title_plain = f"🔧 {func_name}"
    if len(title_plain) + 4 <= width - 2:
        title_line = (
            f" {c(title_plain, colour, bold=True)}"
            f"{' ' * (width - len(title_plain) - 1)} "
        )
    else:
        title_line = f" {title_plain} "

    # ── Tool-call args section
    _call_label = c("Call: ", BOLD)
    call_lines = _wrap_text(_call_label + args_str, width - 2)
    if not call_lines:
        call_lines = [_call_label]

    # ── Divider label
    sep_label = c(" Result ", BOLD)
    pad_right = max(0, width - _safe_len(sep_label) - 2)
    sep_line = f" {sep_label}{' ' * pad_right} "

    # ── Result section (truncated for display)
    result_str = str(result).strip()
    if not result_str:
        result_lines = [c("(empty result)", DIM)]
    else:
        _result_label = c("Output: ", BOLD)
        result_lines = _wrap_text(_result_label + _trunc_for_display(result_str), width - 2)

    # ── Assemble all body lines
    body_lines: list[str] = []
    for line in call_lines:
        body_lines.append(line)
    body_lines.append(sep_line)
    for line in result_lines:
        body_lines.append(line)

    parts = [border_top, title_line]
    for bl in body_lines:
        pad = " " * (width - _safe_len(bl) - 2)
        parts.append(f" {bl}{pad} ")
    parts.append(border_bot)

    print("\n" + "\n".join(parts) + RESET + "\n")


def display_tool_success(func_name: str, message: str) -> None:
    """Print a one-line success/confirmation for tools that don't return text."""
    print(c(f"   → {message}", GREEN))


def display_error(message: str) -> None:
    """Print an error message in red."""
    print(c(f"Error: {message}", RED))
