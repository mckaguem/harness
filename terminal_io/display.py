"""High-level display helpers using Rich for rendering."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
import json

from .speed import _format_speed

console = Console()


def print_system(title: str, message: str) -> None:
    """Print a system-level notification panel."""
    console.print(Panel(message, title=title, border_style="magenta"))


def display_user_prompt(user_input: str) -> None:
    """Print a panel showing what the user typed (with char count)."""
    title = f"📝 Your Prompt ({len(user_input)} chars)"
    console.print(Panel(user_input, title=title, border_style="cyan"))


def display_tool_call(func_name: str, args_str: str) -> None:
    """Print a tool-call panel showing the function name and its arguments."""
    # Try to format args as JSON if possible, otherwise plain text
    try:
        parsed = json.loads(args_str)
        syntax = Syntax(json.dumps(parsed, indent=2), "json", theme="monokai")
        console.print(Panel(syntax, title=f"🔧 {func_name}", border_style="blue"))
    except (json.JSONDecodeError, TypeError):
        console.print(Panel(args_str, title=f"🔧 {func_name}", border_style="blue"))


def _theme_border(theme: str) -> str:
    """Return a Rich border style string for the given theme."""
    return {
        "error": "red",
        "status": "green",
        "read": "blue",
        "write": "cyan",
        "command": "yellow",
    }.get(theme, "white")


def _panel_title(func_name: str, title_override: str | None) -> str:
    """Build the panel title from either an override or a default format."""
    if title_override is not None and title_override:
        return title_override
    # Legacy fallback: derive from function name.
    return f"✅ {func_name} Result"


def display_tool_result(func_name: str, result_type: str, content) -> None:
    """Print a truncated tool-result panel with syntax highlighting.

    Args:
        func_name: Name of the tool that produced the result.
        result_type: Rich-recognized format type (e.g., ``"python"``, ``"json"``).
                     Use ``"_error_"`` to render a distinct error panel.
        content: The plain text content without ANSI codes, OR a :class:`ToolResult`
                 object from tools that opt into the new structured return format.

    Behavior
    --------
    If the result is longer than 5 lines, only the first 5 are shown followed by
    an ellipsis line indicating how many lines were truncated (e.g. ``... [8 lines truncated]``).
    """
    # Unwrap ToolResult if present; otherwise treat content as a legacy string.
    if isinstance(content, object) and hasattr(content, 'llm_text'):
        display_content = str(content.display_text)
        result_type = content.type_tag or result_type
        title_override = content.title or func_name
        theme = content.theme
    else:
        display_content = str(content)
        title_override = None
        # Derive a default theme from the legacy type_tag.
        if result_type == "_error_":
            theme = "error"
        elif result_type in ("read", "write", "command"):
            theme = result_type
        else:
            theme = "read"  # default for unknown types
    
    # Truncate if longer than 5 lines.
    lines = display_content.splitlines()
    if len(lines) > 5:
        truncated_count = len(lines) - 5
        display_content = '\n'.join(lines[:5]) + f'\n... [{truncated_count} line{"s" if truncated_count != 1 else ""} truncated]'
    
    border_style = _theme_border(theme)
    title = _panel_title(func_name, title_override)

    if theme == "error":
        # Render errors distinctly — red border, red text, no syntax highlight.
        console.print(Panel(
            f"[red]{display_content}[/red]",
            title=title,
            border_style=border_style
        ))
    else:
        # Apply Rich Syntax highlighting for the appropriate format.
        syntax = Syntax(display_content, result_type, theme="monokai")
        console.print(Panel(syntax, title=title, border_style=border_style))


def display_tool_call_with_result(func_name: str, args_str: str, result: str) -> None:
    """Print a single combined panel containing the tool call and its result."""
    # Format call and result sections
    content = f"**Call:**\n```json\n{args_str}\n```\n\n---\n\n**Result:**\n```text\n{str(result)}\n```"
    console.print(Panel(content, title=f"🔧 {func_name}", border_style="blue", expand=False))


def display_tool_success(func_name: str, message: str) -> None:
    """Print a one-line success/confirmation for tools that don't return text."""
    console.print(f"[green]   → {message}[/green]")


def display_error(message: str) -> None:
    """Print an error message in red."""
    console.print(f"[red bold]Error:[/red bold] {message}")


def display_agent_response(content: str, response: dict = {}, context_length: int = 0,
                           prompt_token_count: int | None = None) -> None:
    """Print the agent's text response along with token-speed stats."""
    from rich.markdown import Markdown
    
    markdown_obj = Markdown(content)
    console.print(Panel(markdown_obj, title="🤖 Agent Response", border_style="green"))
    speed_info = _format_speed(response, context_length, prompt_token_count)
    if speed_info:
        console.print(speed_info)
