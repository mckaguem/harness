"""edit_file — apply a single search-and-replace edit to a file."""

from harness_core.tools.utils import is_safe_path, _strip_ansi, make_error_result
from harness_core.tools.tool_result import ToolResult


def edit_file(filename: str, old_text: str, new_text: str) -> ToolResult:
    """Apply a single search-and-replace edit to *filename*.

    ``old_text`` must be an exact, unique snippet that appears in the file;
    only its first occurrence is replaced with ``new_text``. If ``old_text``
    is not found, an error result is returned and the file remains unchanged
    (atomic per call).
    """
    if not old_text or not isinstance(old_text, str):
        return make_error_result("`old_text` is invalid or missing.")
    if new_text is None or not isinstance(new_text, str):
        return make_error_result("`new_text` is invalid or missing.")

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

    idx = content.find(old_text)
    if idx == -1:
        snippet_lines = old_text.splitlines()[:3]
        snippet_preview = "\n".join(snippet_lines)
        preview = (snippet_preview + "...") if len(snippet_lines) > 3 else snippet_preview
        return make_error_result(
            f"`old_text` not found in {filename}. "
            f"Searched for:\n    {preview}\n\n"
            f"Adjust the old_text (include surrounding context if needed) and retry."
        )

    # Apply replacement
    content = content[:idx] + new_text + content[idx + len(old_text):]
    lines_replaced = old_text.count('\n') + 1

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

    result_msg = f"Edit: replaced {lines_replaced} line(s) in {filename}"
    return ToolResult(
        llm_text=result_msg,
        display_text=result_msg,
        type_tag="diff",
        title="✏️ Edit File",
        theme="write"
    )


def summary(filename: str, old_text: str | None = None, new_text: str | None = None) -> str:
    """Return a one-line summary of the edit_file call."""
    return f"edit_file: {filename} (1 edit)"


function_def = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": (
            "Make a precise edit to an existing file by replacing exact text strings. "
            "Provide `old_text` — a unique snippet that must appear exactly as-is in the file — "
            "and `new_text`, which replaces it. Only the first occurrence of `old_text` is replaced. "
            "If `old_text` does not match, the edit fails so you can adjust before retrying."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "The file to edit (within cwd, or under /tmp)."},
                "old_text": {"type": "string", "description": "Exact text to find. Include surrounding lines for uniqueness."},
                "new_text": {"type": "string", "description": "Text that replaces `old_text`."}
            },
            "required": ["filename", "old_text", "new_text"]
        }
    }
}
