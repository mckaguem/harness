"""read_file — read the contents of a file in the current working directory."""

from pathlib import Path
from rich.console import Console
console = Console()
from tools.utils import is_safe_path, _strip_ansi, make_error_result
from tools.tool_result import ToolResult


# Extension → Rich syntax format mapping for auto-detection.
_EXT_FORMATS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".less": "less",
    ".md": "markdown",
    ".sh": "bash",
    ".bash": "bash",
    ".sql": "sql",
    ".xml": "xml",
    ".rb": "ruby",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".rs": "rust",
    ".go": "go",
    ".php": "php",
}


def _detect_format(filename: str) -> str:
    """Detect Rich syntax format from file extension."""
    ext = Path(filename).suffix.lower()
    return _EXT_FORMATS.get(ext, "text")


def read_file(filename: str) -> ToolResult:
    """Read a file and return its contents with auto-detected format.

    Returns:
        A ``ToolResult`` containing the formatted content (type + content joined
        by " | "), or an error result for failures.
    """
    if not is_safe_path(filename):
        return make_error_result("Path traversal detected. You may only read from within the project directory.")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        fmt = _detect_format(filename)
        console.print(f"[dim]Read {filename} ({len(content)} chars)[/dim]")
        result_str = f"{fmt} | {content}"
        return ToolResult(llm_text=result_str, display_text=result_str, type_tag=fmt, title="📄 Read File", theme="info")
    except FileNotFoundError:
        return make_error_result(f"File {filename} not found.")
    except Exception as e:
        return make_error_result(f"Error reading file: {e}")


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
