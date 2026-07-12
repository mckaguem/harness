"""update_memory — append to or rewrite the project's MEMORY.md persistent memory file."""

import json
from pathlib import Path

from harness_core.memory import MEMORY_FILENAME, get_memory_path
from harness_core.tools.tool_result import ToolResult
from harness_core.tools.utils import make_error_result
from harness_core.utils import project_root


def update_memory(content: str, mode: str = "replace") -> ToolResult:
    """Update the persistent project memory file (MEMORY.md).

    The memory file lives at the project root and its contents are auto-injected
    into every agent's system prompt, surviving context compression and reloads.

    Use mode ``"replace"`` to overwrite the file (or create it) and ``"append"``
    to add a new section. After a successful write, the new content will appear in
    the system prompt on subsequent sessions.

    Args:
        content: The text to write. For mode ``"append"`` a blank-line separator
            is added before the new content.
        mode: ``"replace"`` (default) to overwrite MEMORY.md, or ``"append"`` to
            add to it.

    Returns:
        A :class:`~harness_core.tools.tool_result.ToolResult` describing the outcome.
    """
    if mode not in ("replace", "append"):
        return make_error_result(
            f"Invalid mode '{mode}'. Use 'replace' or 'append'.",
            title="Update Memory",
        )

    try:
        root = project_root()
    except FileNotFoundError:
        root = Path.cwd()

    path = root / MEMORY_FILENAME

    try:
        if mode == "append" and path.is_file():
            existing = path.read_text(encoding="utf-8")
            new_text = f"{existing.rstrip()}\n\n{content.rstrip()}\n"
        else:
            new_text = f"{content.rstrip()}\n"

        path.write_text(new_text, encoding="utf-8")
        bytes_written = len(new_text.encode("utf-8"))
        result_str = json.dumps({
            "status": "ok",
            "filename": str(path),
            "mode": mode,
            "bytes": bytes_written,
        })
        return ToolResult(
            llm_text=result_str,
            display_text=(
                f"### 🧠 Memory Updated\n\n"
                f"Wrote `{path}` (mode={mode}, {bytes_written} bytes)."
            ),
            type_tag="json",
            title="🧠 Update Memory",
            theme="write",
        )
    except Exception as e:
        return make_error_result(f"Error updating memory: {e}", title="Update Memory")


def summary(content: str, mode: str = "replace") -> str:
    """Return a one-line summary of the update_memory call."""
    return f"update_memory: mode={mode} ({len(content)} chars)"


function_def = {
    "type": "function",
    "function": {
        "name": "update_memory",
        "description": (
            "Maintain the project's persistent memory file (MEMORY.md) at the "
            "project root. Its contents are auto-injected into every agent's "
            "system prompt and survive context compression and session reloads. "
            "Use this to record durable facts, decisions, and conventions the "
            "agent should remember across runs. Use mode 'replace' to overwrite "
            "the file or 'append' to add a new section."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The memory text to write or append.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["replace", "append"],
                    "description": (
                        "How to apply the content: 'replace' (default) overwrites "
                        "MEMORY.md; 'append' adds a new section to it."
                    ),
                },
            },
            "required": ["content"],
        },
    },
}
