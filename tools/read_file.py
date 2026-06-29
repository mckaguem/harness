"""read_file — read the contents of a file in the current working directory."""


def read_file(filename: str) -> str:
    """Read a file if it is within the current working directory."""
    from terminal_io import c, RED, DIM
    from tools.utils import is_safe_path

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


function_def = {
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
}
