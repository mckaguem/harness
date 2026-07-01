"""read_file — read the contents of a file in the current working directory."""


def read_file(filename: str) -> str:
    """Read a file if it is within the current working directory."""
    from rich.console import Console
    console = Console()
    from tools.utils import is_safe_path


    if not is_safe_path(filename):
        return (
            "Error: Path traversal detected. You may only read from the current directory."
        )

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        console.print(f"[dim]Read {filename} ({len(content)} chars)[/dim]")
        return content
    except FileNotFoundError:
        return f"Error: File {filename} not found."
    except Exception as e:
        return f"Error reading file: {str(e)}"


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
