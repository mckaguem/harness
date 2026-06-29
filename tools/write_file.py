"""write_file — write or overwrite a file in the current working directory."""


def write_file(filename: str, content: str) -> str:
    """Write to a file if it is within the current working directory."""
    from terminal_io import c, RED, GREEN
    from tools.utils import is_safe_path

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
