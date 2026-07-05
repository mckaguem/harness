"""Shared utilities for tools — path safety checks, ANSI stripping, and error formatting."""

import re
from pathlib import Path
from tools.tool_result import ToolResult


def is_safe_path(filename: str) -> bool:
    """Ensure the target path is strictly within the current working directory."""
    try:
        cwd = Path.cwd().resolve()
        target = (Path.cwd() / filename).resolve()
        return target.is_relative_to(cwd)
    except Exception:
        return False


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences and inline color tags from *text*."""
    # Strip ANSI escape codes like \033[92m or \033[1;33m
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    # Strip tag-style markers like [GREEN], [/GREEN], [BOLD]
    text = re.sub(r'\[/?[A-Z_]+\]', '', text)
    return text


def make_error_result(message: str, title: str = "Error") -> ToolResult:
    """Create a standardized error ToolResult.
    
    This helper centralizes the common pattern of returning error results across
    all tool implementations, ensuring consistent formatting and reducing boilerplate.
    
    Args:
        message: The error message to display (will be ANSI-stripped).
        title: Optional custom title. Defaults to "Error".
    
    Returns:
        A ToolResult with theme="error", type_tag="text", and the formatted message.
    """
    return ToolResult(
        llm_text=_strip_ansi(message),
        display_text=_strip_ansi(message),
        type_tag="text",
        title=title,
        theme="error"
    )
