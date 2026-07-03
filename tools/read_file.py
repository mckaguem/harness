"""read_file — read the contents of a file in the current working directory."""

from pathlib import Path
from rich.console import Console
console = Console()
from tools.utils import is_safe_path, _strip_ansi
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
        msg = _strip_ansi("Error: Path traversal detected. You may only read from the current directory.")
        return ToolResult(llm_text=msg, display_text=msg, type_tag="text", title="🚫 Error", theme="error")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        fmt = _detect_format(filename)
        console.print(f"[dim]Read {filename} ({len(content)} chars)[/dim]")
        result_str = f"{fmt} | {content}"
        return ToolResult(llm_text=result_str, display_text=result_str, type_tag=fmt, title="📄 Read File")
    except FileNotFoundError:
        msg = _strip_ansi(f"Error: File {filename} not found.")
        return ToolResult(llm_text=msg, display_text=msg, type_tag="text", title="🚫 Error", theme="error")
    except Exception as e:
        msg = f"Error reading file: {e}"
        return ToolResult(llm_text=msg, display_text=msg, type_tag="text", title="🚫 Error", theme="error")


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
