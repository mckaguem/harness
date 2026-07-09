"""Configuration resolution — project and global .harness_py paths."""

import os
from pathlib import Path

# Import project_root from utils
from utils import project_root

# ---------------------------------------------------------------------------
# Centralized constants for the harness codebase.
# ---------------------------------------------------------------------------

#: Valid task lifecycle statuses (must remain immutable).
VALID_TASK_STATUSES = ("pending", "in_progress", "completed", "failed")

#: Default model context length used when runtime detection is unavailable.
DEFAULT_CONTEXT_LENGTH = 8192

#: Subdirectories within .harness_py for component discovery.
_SKILLS_DIR = "skills"
_AGENTS_DIR = "agents"


def get_project_dir() -> Path:
    """Return the project config directory ``project_root/.harness_py/``."""
    # Find the project root directory using common markers
    root = project_root()
    return (root / ".harness_py").resolve()


def get_global_dir() -> Path:
    """Return the global config directory, defaulting to ``~/.harness_py/``.

    Override with the ``HARNESS_PY_HOME`` environment variable.
    """
    override = os.environ.get("HARNESS_PY_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".harness_py"


def get_harness_py_dir() -> tuple[Path, Path]:
    """Return both harness_py directories as a ``(project_dir, global_dir)`` tuple.

    Both are :class:`Path` objects with ``agents/`` and ``skills/`` subdirectories
    available inside them. Project dir takes precedence over global when
    discovering skills and agents with the same name.
    """
    return get_project_dir(), get_global_dir()


def get_discovery_dirs(subdir: str) -> list[Path]:
    """Return ordered discovery directories for a given component (skills/agents).

    This helper centralizes the repeated pattern of resolving both project and
    global .harness_py subdirectories in one call, ensuring consistent ordering
    (project first) across all discovery modules.

    Args:
        subdir: The subdirectory name within ``.harness_py/`` to discover
            (e.g. ``"skills"`` or ``"agents"``).

    Returns:
        An ordered list of :class:`Path` objects — project first, then global.
    """
    project_dir, global_dir = get_harness_py_dir()
    return [project_dir / subdir, global_dir / subdir]
