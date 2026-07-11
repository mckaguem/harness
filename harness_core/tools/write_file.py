"""write_file — write or overwrite a file in the current working directory."""

import json
from harness_core.tools.utils import is_safe_path, _strip_ansi, make_error_result
from harness_core.tools.tool_result import ToolResult


def write_file(filename: str, content: str) -> ToolResult:
    """Write to a file if it is within the current working directory.

    Returns:
        A ``ToolResult`` containing JSON-encoded status data and filename/bytes info,
        or an error result for failures.
    """
    if not is_safe_path(filename):
        return make_error_result("Path traversal detected. You may only write to within the project directory.")

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        size = len(content.encode('utf-8'))
        result_str = json.dumps({"status": "ok", "filename": filename, "bytes": size})
        return ToolResult(llm_text=result_str, display_text=result_str, type_tag="json", title="Write File", theme="write")
    except Exception as e:
        return make_error_result(f"Error writing to file: {e}")


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
