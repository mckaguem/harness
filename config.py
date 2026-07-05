"""Configuration resolution — project and global .harness_py paths."""

import os
from pathlib import Path


def get_project_dir() -> Path:
    """Return the project config directory ``cwd/.harness_py/``."""
    return (Path.cwd() / ".harness_py").resolve()


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
