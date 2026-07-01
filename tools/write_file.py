"""write_file — write or overwrite a file in the current working directory."""

import json
from tools.utils import is_safe_path, _strip_ansi


def write_file(filename: str, content: str) -> tuple:
    """Write to a file if it is within the current working directory.

    Returns:
        A ``(type, text)`` tuple.  ``type`` is one of Rich's recognised
        syntax-highlighting formats (here always ``"text"`` for status messages)
        or ``"_error_"`` to signal a distinct error rendering in the display layer.
    """
    if not is_safe_path(filename):
        return (
            "_error_",
            _strip_ansi("Error: Path traversal detected. You may only write to the current directory."),
        )

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        size = len(content.encode('utf-8'))
        return (
            "json",
            _strip_ansi(json.dumps({"status": "ok", "filename": filename, "bytes": size}))
        )
    except Exception as e:
        return ("_error_", f"Error writing to file: {e}")


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
