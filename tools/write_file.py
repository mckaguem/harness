"""write_file — write or overwrite a file in the current working directory."""


def write_file(filename: str, content: str) -> str:
    """Write to a file if it is within the current working directory."""
    from tools.utils import is_safe_path


    if not is_safe_path(filename):
        return (
            "Error: Path traversal detected. You may only write to the current directory."
        )

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: Wrote to {filename}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"


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
