"""edit_file — apply ordered search-and-replace edits to a file."""


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
    from terminal_io import c, RED, DIM, GREEN
    from tools.utils import is_safe_path

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


function_def = {
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
}
