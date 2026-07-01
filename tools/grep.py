"""grep — search for patterns across files in the current working directory."""

import os
import re
from pathlib import Path
from tools.utils import _strip_ansi


def grep(
    pattern: str,
    path: str,
    use_regex: bool = False,
    file_filter: str | None = None,
    max_matches: int = 50,
) -> tuple:
    """Search for *pattern* inside files under the cwd.

    Returns a structured string of matches — one block per hit — plus a summary
    count so you can decide whether to narrow the search.

    Parameters
    ----------
    pattern : str
        Literal substring (default) or Python regex when ``use_regex=True``.
    path : str
        File or directory within cwd to search. Directories are searched
        recursively; binary files and paths under ``__pycache__`` / `.git/` are
        skipped automatically.
    use_regex : bool, optional
        Treat *pattern* as a regex. Defaults to False.
    file_filter : str | None, optional
        Optional glob/suffix filter on filenames (e.g. ``"*.py"``, ``"test_*"``).
    max_matches : int, optional
        Cap the number of matches returned. Defaults to 50.

    Returns
    -------
    tuple[str, str]
        A ``(type, text)`` tuple where type is ``"text"`` for results or errors,
        or ``"_error_"`` to signal a distinct error rendering in the display layer.
    """

    if not pattern:
        return ("_error_", _strip_ansi("Error: `pattern` must be non-empty."))

    if max_matches < 1:
        return ("_error_", _strip_ansi("Error: `max_matches` must be >= 1."))

    cwd = Path.cwd().resolve()
    target = (Path.cwd() / path).resolve()

    # Safety — every candidate path must stay inside cwd.
    if not target.is_relative_to(cwd):
        return (
            "_error_",
            _strip_ansi(
                "Error: Path traversal detected. `path` must be within the current directory."
            ),
        )

    try:
        compiled = re.compile(pattern) if use_regex else None
    except re.error as e:
        return ("_error_", _strip_ansi(f"Error: Invalid regex pattern — {e}"))

    files_to_search: list[Path] = []

    # Decide whether to search a single file or recurse into a directory.
    try:
        if target.is_dir():
            for root, dirs, names in os.walk(target):
                # Prune noisy directories upfront so we don't descend into them.
                dirs[:] = [
                    d for d in dirs
                    if d not in {"__pycache__", ".git"} and not d.startswith(".")
                ]
                for name in sorted(names):
                    full = Path(root) / name
                    # Skip binary files by peeking at the first chunk.
                    if _is_binary(full):
                        continue
                    if file_filter and not _matches_file_filter(name, file_filter):
                        continue
                    try:
                        rel = full.relative_to(cwd)
                        files_to_search.append(rel)
                    except ValueError:
                        # Defensive — shouldn't happen after safety check.
                        pass
        elif target.is_file():
            files_to_search.append(target.relative_to(cwd))
        else:
            return (
                "_error_",
                _strip_ansi(
                    f"Error: `{path}` is not a file or directory in the current workspace."
                ),
            )
    except Exception as e:
        return ("_error_", f"Error scanning path `{path}`: {e}")

    if not files_to_search:
        # Helpful message — tell the user we looked but found nothing to scan.
        filter_note = f" with file_filter=`{file_filter}`" if file_filter else ""
        return (
            "text",
            _strip_ansi(f"No files found under `{path}`{filter_note} to search."),
        )

    matches: list[dict] = []  # {"file": str, "line_no": int, "content": str}

    for rel_path in sorted(files_to_search):
        abs_path = cwd / rel_path
        try:
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                for line_no, raw_line in enumerate(f, start=1):
                    line = raw_line.rstrip('\n\r')
                    hit = compiled.search(line) if compiled else pattern in line
                    if hit and len(matches) < max_matches:
                        matches.append({
                            "file": str(rel_path),
                            "line_no": line_no,
                            "content": line.strip(),
                        })
        except PermissionError as e:
            return ("_error_", _strip_ansi(f"Permission denied reading `{abs_path}`: {e}"))
        except Exception as e:
            # Skip unreadable files gracefully — don't abort the whole search.
            continue

    if not matches:
        return (
            "text",
            _strip_ansi(
                f"No matches found for pattern {'(regex) ' if use_regex else ''}`{pattern}` under `{path}`."
            ),
        )

    lines_out = []
    for m in matches:
        # Format: file:line — content snippet.
        lines_out.append(f"{m['file']}:{m['line_no']}  {m['content']}")

    summary_line = (
        f"Found {len(matches)} match{'es' if len(matches) != 1 else ''}"
        f" for pattern `{pattern}`"
        f" under `{path}`."
        + (f" (limited to {max_matches})" if len(matches) >= max_matches else "")
    )

    return ("text", _strip_ansi("\n".join([summary_line] + lines_out)))


def _is_binary(path: Path) -> bool:
    """Return True if *path* looks like a binary file."""
    try:
        with open(path, 'rb') as f:
            chunk = f.read(8192)
    except Exception:
        return True
    # A null byte in the first 8K is a strong indicator of a binary file.
    return b'\x00' in chunk


def _matches_file_filter(name: str, file_filter: str) -> bool:
    """Check whether *name* matches *file_filter*.

    Supports two forms:
      - glob patterns (e.g. ``"*.py"``, ``"test_*"``) via :func:`fnmatch.fnmatch`.
      - plain suffixes — if the filter has no special characters it's matched as
        a simple suffix, so ``".txt"`` matches any file ending in .txt.
    """
    from fnmatch import fnmatch

    # If the filter looks like a glob (contains *, ?, [) use full matching.
    if any(ch in file_filter for ch in ('*', '?', '[')):
        return fnmatch(name, file_filter)

    # Otherwise treat it as a literal suffix match — useful for extensions like ".py".
    return name.endswith(file_filter)


function_def = {
    "type": "function",
    "function": {
        "name": "grep",
        "description": (
            "Search for a pattern in one or more files within the current working directory. "
            "Useful for finding function definitions, imports, usages, TODOs, etc. Returns "
            "a structured list of matches with file path, line number, and content snippet."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": (
                        "The pattern to search for. Interpreted as a literal string if "
                        "`use_regex` is false, or as a Python regular expression otherwise."
                    )
                },
                "path": {
                    "type": "string",
                    "description": (
                        "File or directory path within cwd to search. If it points to a "
                        "directory, the search recurses into subdirectories (respects "
                        ".gitignore and skips binary files)."
                    )
                },
                "use_regex": {
                    "type": "boolean",
                    "description": "Treat `pattern` as a regex. Defaults to false."
                },
                "file_filter": {
                    "type": "string",
                    "description": (
                        "Optional glob or suffix filter for file names, e.g. '*.py' or "
                        "'test_*'. Ignored when `path` points at a single file."
                    )
                },
                "max_matches": {
                    "type": "integer",
                    "description": (
                        "Cap the number of matches returned. Defaults to 50. Set higher "
                        "for broad searches or lower for targeted ones."
                    )
                }
            },
            "required": ["pattern", "path"]
        }
    }
}
