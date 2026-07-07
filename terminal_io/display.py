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
    """Print a tool-call panel showing the function name and its arguments.

    Renders the call using ``display_message_panel`` with theme="info" and
    result_type="markdown".  Arguments are displayed as key/value parameters
    (the function name itself appears only in the title).
    """
    # First pass: attempt raw JSON parse (do NOT pre-decode newlines, or we'll corrupt the string).
    parsed = None  # default in case parsing fails below.

    try:
        parsed = json.loads(args_str)
        if isinstance(parsed, dict):
            lines: list[str] = []
            for key, value in parsed.items():
                if isinstance(value, list):
                    # Label on its own line
                    lines.append(f"**{key}**:")
                    # Each item as a bullet on separate line
                    for v in value:
                        lines.append(f"- {v}")
                else:
                    val_str = str(value)
                    val_str = val_str.replace("\\n", "\n").replace("\\r", "\r")
                    lines.append(f"**{key}**: {val_str}")
            display_content = "\n\n".join(lines)
        else:
            # List or scalar: render as normal JSON, then decode escaped newlines.
            display_content = json.dumps(parsed, indent=2)
            display_content = display_content.replace("\\n", "\n").replace("\\r", "\r")
    except (json.JSONDecodeError, TypeError, ValueError):
        # Fallback: render raw string with decoded newlines.
        display_content = args_str.replace("\\n", "\n").replace("\\r", "\r")

    title = f"Tool: {func_name}"
    display_message_panel(
        text=display_content,
        theme="status",
        title=title,
        result_type="markdown",
    )


def _theme_border(theme: str) -> str:
    """Return a Rich border style string for the given theme."""
    return {
        "error": "red",
        "status": "purple",
        "info": "green",
        "read": "blue",
        "write": "yellow",
        "command": "cyan",
    }.get(theme, "white")


def _panel_title(func_name: str, title_override: str | None) -> str:
    """Build the panel title from either an override or a default format."""
    if title_override is not None and title_override:
        return title_override
    # Legacy fallback: derive from function name.
    return f"✅ {func_name} Result"


def display_message_panel(text: str, theme: str = "status", title: str = "",
                          result_type: str = "text") -> None:
    """Display a Rich panel with the given text, styled by theme.

    Shared rendering logic for tool-result panels and ad-hoc command output.

    Args:
        text: The content to display inside the panel. Truncated after 5 lines
              unless ``theme == "status"`` (e.g. task lists).
        theme: One of ``"error"``, ``"status"``, ``"info"``, ``"read"``,
               ``"write"``, ``"command"`` — selects the panel border color.
        title: Custom panel title. Falls back to a default if empty.
        result_type: The syntax-highlighting language tag (e.g. ``"markdown"``,
                     ``"json"``, ``"text"``).
    """
    # Truncate if longer than 5 lines (skip truncation for 'status' theme, e.g. task lists).
    display_content = str(text)
    lines = display_content.splitlines()
    if len(lines) > 5 and theme != "status":
        truncated_count = len(lines) - 5
        display_content = '\n'.join(lines[:5]) + f'\n... [{truncated_count} line{"s" if truncated_count != 1 else ""} truncated]'

    border_style = _theme_border(theme)
    panel_title = title if title else "✅ Result"

    # Choose between Markdown rendering and Syntax highlighting based on result_type.
    if theme == "error":
        # Render errors distinctly — red border, red text, no syntax highlight.
        console.print(Panel(
            f"[red]{display_content}[/red]",
            title=panel_title,
            border_style=border_style
        ))
    elif result_type == "markdown":
        # Render as actual Markdown (supports bold, code blocks, etc.) for user-friendly display.
        md_obj = Markdown(display_content)
        console.print(Panel(md_obj, title=panel_title, border_style=border_style))
    else:
        # Apply Rich Syntax highlighting for the appropriate format.
        syntax = Syntax(display_content, result_type, theme="monokai")
        console.print(Panel(syntax, title=panel_title, border_style=border_style))


def display_tool_result(func_name: str, result) -> None:
    """Print a truncated tool-result panel with syntax highlighting.

    Args:
        func_name: Name of the tool that produced the result.
        result: A :class:`ToolResult` object from tools that opt into the new structured return format.

    Behavior
    --------
    If the result is longer than 5 lines, only the first 5 are shown followed by
    an ellipsis line indicating how many lines were truncated (e.g. ``... [8 lines truncated]``).
    """
    # Unwrap ToolResult; content must be a ToolResult object.
    title_override = result.title or func_name
    display_message_panel(
        text=result.display_text,
        theme=result.theme,
        title=title_override,
        result_type=result.type_tag or "text",
    )


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
