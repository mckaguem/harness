"""list_dir — explore directory contents as an LLM-friendly tree view."""

import os
from pathlib import Path
from harness_core.tools.utils import is_safe_path, make_error_result
from harness_core.tools.tool_result import ToolResult
from harness_core.utils import project_root


# Directories that must NEVER be traversed or listed. Descending into these
# (especially node_modules / .git / __pycache__) causes catastrophic token bloat
# in the LLM context, so they are always pruned regardless of parameters.
IGNORE_DIRS = {
    'node_modules',
    '.git',
    '__pycache__',
    '.venv',
    'venv',
    'env',
    'dist',
    'build',
}


def _format_size(size_bytes: int) -> str:
    """Return a concise human-readable size for *size_bytes*.

    Sizes under 1 MB are shown in KB; everything else is shown in MB. Values
    are rounded to the nearest whole unit.
    """
    mb = size_bytes / (1024 * 1024)
    if size_bytes < 1024 * 1024:
        return f"{round(size_bytes / 1024)}KB"
    return f"{round(mb)}MB"


def _build_tree(directory: Path, prefix: str, depth: int, max_depth: int,
                include_hidden: bool) -> list[str]:
    """Recursively render *directory* into ``tree``-style lines.

    Parameters
    ----------
    directory : Path
        The directory to render.
    prefix : str
        The indentation/connector prefix inherited from ancestor levels.
    depth : int
        How many levels deep we already are relative to the search root
        (the root itself is depth 0).
    max_depth : int
        Maximum descent depth; directories at this depth are listed but not
        descended into.
    include_hidden : bool
        Whether entries whose name starts with ``.`` should be included.
    """
    try:
        entries = list(os.scandir(directory))
    except (PermissionError, OSError):
        # Skip directories we cannot read rather than aborting the whole scan.
        return []

    filtered = []
    for entry in entries:
        name = entry.name
        # Always drop the hardcoded token-heavy directories.
        if name in IGNORE_DIRS:
            continue
        # Skip hidden entries unless explicitly requested.
        if not include_hidden and name.startswith('.'):
            continue
        filtered.append(entry)

    # Directories first, then files; each group alphabetical (case-insensitive).
    filtered.sort(key=lambda e: (not e.is_dir(), e.name.lower()))

    lines: list[str] = []
    for index, entry in enumerate(filtered):
        is_last = index == len(filtered) - 1
        connector = '└── ' if is_last else '├── '

        if entry.is_dir():
            if depth + 1 < max_depth:
                lines.append(prefix + connector + entry.name + '/ (Directory)')
                extension = '    ' if is_last else '│   '
                lines.extend(
                    _build_tree(
                        Path(entry.path),
                        prefix + extension,
                        depth + 1,
                        max_depth,
                        include_hidden,
                    )
                )
            else:
                # Reached maximum depth — list the name but do not descend.
                lines.append(
                    prefix + connector + entry.name + '/ (Directory - max depth reached)'
                )
        else:
            try:
                size = _format_size(entry.stat(follow_symlinks=False).st_size)
            except OSError:
                size = '0KB'
            lines.append(prefix + connector + entry.name + f' (File - {size})')

    return lines


def list_dir(path: str = '.', max_depth: int = 2, include_hidden: bool = False) -> ToolResult:
    """Explore directory contents and return an LLM-friendly tree view.

    Walks the directory tree starting at *path* (relative to the project root)
    and renders it using Unicode box-drawing characters, similar to the bash
    ``tree`` command. Token-heavy build directories are always ignored, and the
    descent depth is clamped to keep output bounded.

    Parameters
    ----------
    path : str, optional
        Directory (relative to the project root) to explore. Defaults to ``'.'``.
    max_depth : int, optional
        Maximum descent depth from the root directory. Defaults to 2 and is
        clamped to the range [1, 4].
    include_hidden : bool, optional
        Whether to include entries whose names start with ``.``. Defaults to
        False.

    Returns
    -------
    ToolResult
        A ``ToolResult`` whose ``llm_text`` / ``display_text`` contain the tree,
        or an error result for invalid or unsafe paths.
    """
    # Path safety — refuse anything that escapes the project directory.
    if not is_safe_path(path):
        return make_error_result(
            "Path traversal detected. You may only list directories within the project directory."
        )

    # Resolve the target; is_safe_path() above already guarantees it stays
    # inside the project root, so this is purely for downstream use.
    try:
        cwd = project_root().resolve()
    except FileNotFoundError:
        cwd = Path.cwd().resolve()
    target = (cwd / path).resolve()

    if not target.is_dir():
        return make_error_result(f"`{path}` is not a directory in the current workspace.")

    # Clamp the depth into the safe range [1, 4].
    max_depth = max(1, min(4, max_depth))

    root_name = target.name or str(target)
    lines = [root_name + '/']
    lines.extend(_build_tree(target, '', 0, max_depth, include_hidden))

    result_str = '\n'.join(lines)
    return ToolResult(
        llm_text=result_str,
        display_text=result_str,
        type_tag="text",
        title="📁 List Directory",
        theme="info",
    )


def summary(path: str = '.', max_depth: int = 2, include_hidden: bool = False) -> str:
    """Return a one-line summary of the list_dir call."""
    return f"list_dir: {path} (depth={max_depth}, hidden={include_hidden})"


function_def = {
    "type": "function",
    "function": {
        "name": "list_dir",
        "description": (
            "Explore directory contents. Returns an LLM-friendly tree-structured "
            "view of files and folders. Automatically ignores token-heavy build "
            "directories."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory to explore, relative to the project root. Defaults to '.' (project root)."
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum descent depth from the root directory. Defaults to 2, clamped to a maximum of 4."
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Whether to include entries whose names start with '.'. Defaults to false."
                }
            },
            "required": ["path"]
        }
    }
}
