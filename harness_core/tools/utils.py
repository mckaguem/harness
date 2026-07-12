"""Shared utilities for tools — path safety checks, ANSI stripping, and error formatting."""

import re
from pathlib import Path
from harness_core.tools.tool_result import ToolResult
from harness_core.utils import project_root


def is_safe_path(filename: str) -> bool:
    """Ensure the target path is within an allowed directory.

    Allowed locations are ``/tmp`` (resolving anywhere under it) and the
    project root (found via project markers like ``.git`` or ``.harness_py``;
    falls back to the current working directory if no root is found).

    Paths that resolve outside both ``/tmp`` and the project root are rejected,
    and any unexpected error fails closed (returns ``False``).
    """
    # Any path that resolves under /tmp is always allowed.
    candidate = Path(filename)
    try:
        tmp_target = (Path("/tmp") / filename).resolve() if not candidate.is_absolute() else candidate.resolve()
    except Exception:
        tmp_target = None
    if tmp_target is not None and tmp_target.is_relative_to(Path("/tmp")):
        return True
    
    try:
        # First try to get project root
        root = project_root().resolve()
    except FileNotFoundError:
        # If no project root found, fall back to current working directory
        root = Path.cwd().resolve()
    except Exception:
        # Any other exception, be conservative and return False
        return False
    
    try:
        target = (root / filename).resolve()
        return target.is_relative_to(root)
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
