"""Tool definitions and implementations for the agent."""

import subprocess
import os
import re
from pathlib import Path
from terminal_io import c, RED, GREEN, DIM


AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_bash",
            "description": "Execute a bash command in the terminal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command to run."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file in the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the file."},
                    "content": {"type": "string", "description": "The exact content to write to the file."}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file in the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the file to read."}
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Make precise edits to an existing file by replacing exact text strings. "
                "Each edit specifies `old_text` — a unique snippet that must appear exactly "
                "as-is in the file — and `new_text`, which replaces it. The first match is "
                "replaced. Use multiple edits in one call to make several changes atomically. "
                "If `old_text` does not match, the edit fails so you can adjust before retrying."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The file to edit (within cwd)."},
                    "edits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "old_text": {
                                    "type": "string",
                                    "description": (
                                        "Exact text to find. Include surrounding lines for "
                                        "uniqueness. The literal content must match the file."
                                    )
                                },
                                "new_text": {
                                    "type": "string",
                                    "description": "Text that replaces `old_text`."
                                }
                            },
                            "required": ["old_text", "new_text"]
                        },
                        "description": "Ordered list of search-and-replace edits."
                    }
                },
                "required": ["filename", "edits"]
            }
        }
    },
    {
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
]


def is_safe_path(filename: str) -> bool:
    """Ensure the target path is strictly within the current working directory."""
    try:
        cwd = Path.cwd().resolve()
        target = (Path.cwd() / filename).resolve()
        return target.is_relative_to(cwd)
    except Exception:
        return False


def execute_bash(command: str) -> str:
    """Execute bash command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        return output if output.strip() else "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return c("Error: Command timed out after 30 seconds.", RED)
    except Exception as e:
        return c(f"Execution Error: {str(e)}", RED)


def write_file(filename: str, content: str) -> str:
    """Write to a file if it is within the current working directory."""
    if not is_safe_path(filename):
        return c(
            "Error: Path traversal detected. You may only write to the current directory.",
            RED
        )

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return c(f"Success: Wrote to {filename}", GREEN)
    except Exception as e:
        return c(f"Error writing to file: {str(e)}", RED)


def read_file(filename: str) -> str:
    """Read a file if it is within the current working directory."""
    if not is_safe_path(filename):
        return c(
            "Error: Path traversal detected. You may only read from the current directory.",
            RED
        )

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        print(c(f"Read {filename} ({len(content)} chars)", DIM))
        return content
    except FileNotFoundError:
        return c(f"Error: File {filename} not found.", RED)
    except Exception as e:
        return c(f"Error reading file: {str(e)}", RED)


def edit_file(filename: str, edits: list[dict]) -> str:
    """Apply ordered search-and-replace edits to *filename*.

    Each edit is ``{"old_text": ..., "new_text": ...}``.  The first occurrence of
    ``old_text`` in the current file content is replaced by ``new_text``.
    Edits are applied sequentially so a later edit sees the already-modified
    content — useful for chaining dependent changes.

    If any edit cannot find its ``old_text``, processing stops and an error is
    returned listing what was found vs. expected, so you can adjust and retry.

    Returns a description of successful edits or an error message.
    """
    if not isinstance(edits, list) or len(edits) == 0:
        return c("Error: `edits` must be a non-empty list.", RED)

    # Path safety check once up front.
    if not is_safe_path(filename):
        return c(
            "Error: Path traversal detected. You may only edit files in the current directory.",
            RED
        )

    # Read existing content first — we want a clean error if it doesn't exist.
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return c(f"Error: File {filename} not found.", RED)
    except Exception as e:
        return c(f"Error reading file for editing: {str(e)}", RED)

    original_content = content
    changes_made: list[str] = []

    for i, edit in enumerate(edits):
        old_text = edit.get("old_text")
        new_text = edit.get("new_text")

        if not old_text or not isinstance(old_text, str):
            return c(f"Error: Edit #{i+1} has invalid or missing `old_text`.", RED)
        if new_text is None or not isinstance(new_text, str):
            return c(f"Error: Edit #{i+1} has invalid or missing `new_text`.", RED)

        idx = content.find(old_text)
        if idx == -1:
            # Report the first few lines of what we expected so the caller can fix it.
            snippet_lines = old_text.splitlines()[:3]
            snippet_preview = "\n".join(snippet_lines)
            preview = (snippet_preview + "...") if len(snippet_lines) > 3 else snippet_preview
            return c(
                f"Error: Edit #{i+1} failed — `old_text` not found in {filename}. "
                f"Searched for:\n    {preview}\n\n"
                f"Adjust the old_text (include surrounding context if needed) and retry.",
                RED
            )

        content = content[:idx] + new_text + content[idx + len(old_text):]
        lines_replaced = old_text.count('\n') + 1
        changes_made.append(
            f"Edit #{i+1}: replaced {lines_replaced} line(s) in {filename}"
        )

    if content == original_content:
        return c(f"No effective changes made to {filename}.", DIM)

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        return c(f"Error writing edited file: {str(e)}", RED)

    result = "\n".join(changes_made)
    return c(result, GREEN)


def grep(
    pattern: str,
    path: str,
    use_regex: bool = False,
    file_filter: str | None = None,
    max_matches: int = 50,
) -> str:
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
    str
        A summary line listing file/line/content for each match, followed by a
        count. If no matches are found or an error occurs, returns a message
        indicating that.
    """
    if not pattern:
        return c("Error: `pattern` must be non-empty.", RED)

    if max_matches < 1:
        return c("Error: `max_matches` must be >= 1.", RED)

    cwd = Path.cwd().resolve()
    target = (Path.cwd() / path).resolve()

    # Safety — every candidate path must stay inside cwd.
    if not target.is_relative_to(cwd):
        return c(
            "Error: Path traversal detected. `path` must be within the current directory.",
            RED,
        )

    try:
        compiled = re.compile(pattern) if use_regex else None
    except re.error as e:
        return c(f"Error: Invalid regex pattern — {e}", RED)

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
            return c(
                f"Error: `{path}` is not a file or directory in the current workspace.",
                RED,
            )
    except Exception as e:
        return c(f"Error scanning path `{path}`: {e}", RED)

    if not files_to_search:
        # Helpful message — tell the user we looked but found nothing to scan.
        filter_note = f" with file_filter=`{file_filter}`" if file_filter else ""
        return (
            c(f"No files found under `{path}`{filter_note} to search.", DIM)
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
            return c(f"Permission denied reading `{abs_path}`: {e}", RED)
        except Exception as e:
            # Skip unreadable files gracefully — don't abort the whole search.
            continue

    if not matches:
        return (
            f"No matches found for pattern {'(regex) ' if use_regex else ''}"
            f"`{pattern}` under `{path}`."
        )

    lines_out = []
    for m in matches:
        # Format: file:line — content snippet.
        lines_out.append(f"{c(m['file'], DIM)}:{m['line_no']}  {m['content']}")

    summary_line = (
        c(
            f"Found {len(matches)} match{'es' if len(matches) != 1 else ''}"
            f" for pattern `{pattern}`",
            GREEN,
        )
        + f" under `{path}`."
        + (c(f" (limited to {max_matches})", DIM) if len(matches) >= max_matches else "")
    )

    return "\n".join([summary_line] + lines_out)


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
