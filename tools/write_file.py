"""write_file — write or overwrite a file in the current working directory."""

import json
from tools.utils import is_safe_path, _strip_ansi
from tools.tool_result import ToolResult


def write_file(filename: str, content: str) -> ToolResult:
    """Write to a file if it is within the current working directory.

    Returns:
        A ``ToolResult`` containing JSON-encoded status data and filename/bytes info,
        or an error result for failures.
    """
    if not is_safe_path(filename):
        msg = _strip_ansi("Error: Path traversal detected. You may only write to the current directory.")
        return ToolResult(llm_text=msg, display_text=msg, type_tag="text", title="🚫 Error", theme="error")

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        size = len(content.encode('utf-8'))
        result_str = json.dumps({"status": "ok", "filename": filename, "bytes": size})
        return ToolResult(llm_text=result_str, display_text=result_str, type_tag="json", title="✅ Write File")
    except Exception as e:
        msg = f"Error writing to file: {e}"
        return ToolResult(llm_text=msg, display_text=msg, type_tag="text", title="🚫 Error", theme="error")


function_def = {
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
}
