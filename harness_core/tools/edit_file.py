"""edit_file — apply search-and-replace edits to a file.

The tool accepts either a single ``edit`` dict or a list of edits via ``edits``.
Both forms are supported so the documented schema (which advertises an
``edits`` array) works, while the simpler single-``edit`` call remains valid.
"""

from harness_core.tools.utils import is_safe_path, _strip_ansi, make_error_result
from harness_core.tools.tool_result import ToolResult


def edit_file(filename: str, edit: dict = None, edits: list = None) -> ToolResult:
    """Apply search-and-replace edits to *filename*.

    Each edit must be a dictionary with the keys ``old_text`` and ``new_text``.
    Only the first occurrence of ``old_text`` is replaced per edit. Edits are
    applied in order; if any edit cannot be applied, an error result is returned
    and the file remains unchanged (atomic per call).

    Either provide a single edit via ``edit``, or a list of edits via ``edits``.
    If both are provided, ``edits`` takes precedence.
    """
    # Normalize to a list of edits.
    edit_list = edits if edits is not None else []
    if edit is not None:
        edit_list = [edit] + list(edit_list)

    if not edit_list:
        return make_error_result(
            "You must provide at least one edit via `edit` (a single dict) "
            "or `edits` (a list of dicts), each with 'old_text' and 'new_text'."
        )

    # Path safety check once up front.
    if not is_safe_path(filename):
        return make_error_result("Path traversal detected. You may only edit files within the project directory.")

    # Read existing content first — we want a clean error if it doesn't exist.
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return make_error_result(f"File {filename} not found.")
    except Exception as e:
        return make_error_result(f"Error reading file for editing: {e}")

    original_content = content
    results = []

    for i, e in enumerate(edit_list, start=1):
        if not isinstance(e, dict):
            return make_error_result(f"Edit #{i} must be a dictionary with 'old_text' and 'new_text'.")

        old_text = e.get('old_text')
        new_text = e.get('new_text')
        if not old_text or not isinstance(old_text, str):
            return make_error_result(f"Edit #{i} has invalid or missing `old_text`.")
        if new_text is None or not isinstance(new_text, str):
            return make_error_result(f"Edit #{i} has invalid or missing `new_text`.")

        idx = content.find(old_text)
        if idx == -1:
            snippet_lines = old_text.splitlines()[:3]
            snippet_preview = "\n".join(snippet_lines)
            preview = (snippet_preview + "...") if len(snippet_lines) > 3 else snippet_preview
            return make_error_result(
                f"Edit #{i} failed — `old_text` not found in {filename}. "
                f"Searched for:\n    {preview}\n\n"
                f"Adjust the old_text (include surrounding context if needed) and retry."
            )

        # Apply replacement
        content = content[:idx] + new_text + content[idx + len(old_text):]
        lines_replaced = old_text.count('\n') + 1
        results.append(f"Edit #{i}: replaced {lines_replaced} line(s)")

    if content == original_content:
        return ToolResult(
            llm_text=_strip_ansi(f"No effective changes made to {filename}."),
            display_text=_strip_ansi(f"No effective changes made to {filename}."),
            type_tag="text",
            title="📝 Edit File",
            theme="info"
        )

    # Write the modified content back to disk
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        return make_error_result(f"Error writing edited file: {e}")

    result_msg = "; ".join(results) + f" in {filename}"
    return ToolResult(
        llm_text=result_msg,
        display_text=result_msg,
        type_tag="diff",
        title="✏️ Edit File",
        theme="write"
    )


def summary(filename: str, edit: dict = None, edits: list = None) -> str:
    """Return a one-line summary of the edit_file call."""
    edit_count = len(edits) if edits else (1 if edit else 0)
    return f"edit_file: {filename} ({edit_count} edit{'s' if edit_count != 1 else ''})"


function_def = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": (
            "Make a precise edit to an existing file by replacing exact text strings. "
            "Provide one or more edits via the `edits` array (or a single `edit` dict). "
            "Each edit specifies `old_text` — a unique snippet that must appear exactly as-is in the file — "
            "and `new_text`, which replaces it. Edits are applied in order; only the first occurrence "
            "of each `old_text` is replaced. If `old_text` does not match, the edit fails so you can adjust before retrying."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "The file to edit (within cwd)."},
                "edit": {
                    "type": "object",
                    "description": "A single edit (convenience alternative to `edits`).",
                    "properties": {
                        "old_text": {"type": "string", "description": "Exact text to find. Include surrounding lines for uniqueness."},
                        "new_text": {"type": "string", "description": "Text that replaces `old_text`."}
                    },
                    "required": ["old_text", "new_text"]
                },
                "edits": {
                    "type": "array",
                    "description": "One or more edits to apply in order.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "old_text": {"type": "string", "description": "Exact text to find. Include surrounding lines for uniqueness."},
                            "new_text": {"type": "string", "description": "Text that replaces `old_text`."}
                        },
                        "required": ["old_text", "new_text"]
                    }
                }
            },
            "required": ["filename"]
        }
    }
}
