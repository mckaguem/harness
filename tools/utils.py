"""Shared utilities for tools — path safety checks and ANSI stripping."""

import re
from pathlib import Path


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
