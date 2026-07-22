"""Persistent project memory (MEMORY.md).

The harness can maintain a durable ``MEMORY.md`` file at the project root. Its
contents are auto-injected into every agent's system prompt (so they survive
context compression and session reloads), and the :mod:`harness_core.tools.update_memory`
tool lets an agent append to or rewrite it while working.

This is the agentic "external memory" pattern: a small, self-maintained notes
file that outlives any single conversation and is orthogonal to (and complementary
with) the session-compression pipeline.
"""

import logging
from pathlib import Path

from harness_core.utils import project_root

logger = logging.getLogger(__name__)

MEMORY_FILENAME = "MEMORY.md"


def get_memory_path() -> Path | None:
    """Return the path to ``MEMORY.md`` in the project root, or ``None`` if absent.

    Uses :func:`harness_core.utils.project_root` to locate the project root; falls
    back to the current working directory if no project markers are found (so the
    memory file still resolves inside test environments).
    """
    try:
        root = project_root()
    except FileNotFoundError:
        root = Path.cwd()
    path = root / MEMORY_FILENAME
    return path if path.is_file() else None


def read_memory() -> str | None:
    """Read the contents of ``MEMORY.md`` (stripped), or ``None`` if absent."""
    path = get_memory_path()
    if path is None:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.exception("Failed to load memory file at %s", path)
        return None
    return text.strip()


def memory_section(memory: str | None = None) -> str:
    """Build the system-prompt section for *memory*.

    Returns an empty string when *memory* is empty/``None`` so callers can append
    it unconditionally without injecting a dangling header.
    """
    if not memory:
        return ""
    return (
        "\n\n## Persistent Project Memory (MEMORY.md)\n"
        "The following durable notes were recorded in the project's MEMORY.md "
        "file by the agent across prior sessions. Treat it as long-term context "
        "that survives conversation compression and session reloads.\n\n"
        f"{memory}\n"
    )
