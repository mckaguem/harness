"""High-level display helpers — thin wrappers that coordinate boxes, markdown, etc."""


from .colors import c, GREEN, RED
from .boxes import print_box
from .trunc import _trunc_for_display


def print_system(title: str, message: str) -> None:
    """Print a system-level notification box."""
    print_box(title, message, style="system")


def display_user_prompt(user_input: str) -> None:
    """Print a box showing what the user typed (with char count)."""
    print_box(f"📝 Your Prompt ({len(user_input)} chars)", user_input, style="user")


def display_tool_call(func_name: str, args_str: str) -> None:
    """Print a tool-call box showing the function name and its arguments."""
    print_box(f"🔧 {func_name}", args_str, style="tool_call")


def display_tool_result(func_name: str, result: str) -> None:
    """Print a truncated tool-result box (full result is kept separately)."""
    display_result = _trunc_for_display(str(result))
    print_box(f"✅ {func_name} Result", display_result, style="tool_result")


def display_tool_success(func_name: str, message: str) -> None:
    """Print a one-line success/confirmation for tools that don't return text."""
    print(c(f"   → {message}", GREEN))


def display_error(message: str) -> None:
    """Print an error message in red."""
    print(c(f"Error: {message}", RED))
