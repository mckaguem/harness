"""read_file — read the contents of a file in the current working directory."""

from pathlib import Path
from rich.console import Console
console = Console()
from harness_core.tools.utils import is_safe_path, _strip_ansi, make_error_result
from harness_core.tools.tool_result import ToolResult


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


def read_file(filename: str, offset: int, limit: int) -> ToolResult:
    """Read a file and return its contents with auto-detected format. Supports offset and limit parameters to read specific line ranges.

    Returns:
        A ``ToolResult`` containing the formatted content (type + content joined
        by " | "), or an error result for failures.
    """
    # Ensure the path is inside the project directory
    if not is_safe_path(filename):
        return make_error_result("Path traversal detected. You may only read from within the project directory.")

    # Validate offset and limit parameters
    if offset < 0:
        return make_error_result("Offset must be non-negative.")
    if limit <= 0:
        return make_error_result("Limit must be positive.")
    if limit > 300:
        return make_error_result("Limit cannot exceed 300 lines.")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            # Slice the requested range
        selected = all_lines[offset:offset + limit]
        # content variable no longer needed for new output format
        # Build XML-like output with line numbers and metadata
        total_lines = len(all_lines)
        start_line = offset + 1
        end_line = min(offset + limit, total_lines)
        # Prepare lines with their original numbers
        numbered_lines = []
        for idx, line_content in enumerate(selected, start=start_line):
            # Strip trailing newline to avoid double spacing
            numbered_lines.append(f"{idx}: {line_content.rstrip()}")
        lines_block = "\n".join(numbered_lines)
        result_str = f'<file path="{filename}" lines="{start_line}-{end_line}" total_lines="{total_lines}">\n{lines_block}\n</file>'
        return ToolResult(llm_text=result_str, display_text=result_str, type_tag="xml", title="📄 Read File", theme="info")
    except FileNotFoundError:
        return make_error_result(f"File {filename} not found.")
    except Exception as e:
        return make_error_result(f"Error reading file: {e}")


def summary(filename: str, offset: int, limit: int) -> str:
    """Return a one-line summary string for read_file."""
    return f"read_file: {filename} (lines {offset+1}-{offset+limit})"


function_def = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a file in the current working directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "The name of the file to read."},
                "offset": {"type": "integer", "description": "Zero‑based line number to start reading from."},
                "limit": {"type": "integer", "description": "Maximum number of lines to read (max 300)."}
            },
            "required": ["filename", "offset", "limit"]
        }
    }
}
