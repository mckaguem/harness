"""High-level display helpers using Rich for rendering."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
import json

from .trunc import _trunc_for_display, MAX_DISPLAY_LINES
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


def display_tool_result(func_name: str, result_type: str, content: str) -> None:
    """Print a truncated tool-result panel with syntax highlighting.

    Args:
        func_name: Name of the tool that produced the result.
        result_type: Rich-recognized format type (e.g., ``"python"``, ``"json"``).
                     Use ``"_error_"`` to render a distinct error panel.
        content: The plain text content without ANSI codes.
    """
    display_content = _trunc_for_display(content)
    
    if result_type == "_error_":
        # Render errors distinctly — red border, red text, no syntax highlight
        console.print(Panel(
            f"[red]{display_content}[/red]",
            title=f"❌ {func_name} Error",
            border_style="red"
        ))
    else:
        # Apply Rich Syntax highlighting for the appropriate format
        syntax = Syntax(display_content, result_type, theme="monokai")
        console.print(Panel(syntax, title=f"✅ {func_name} Result", border_style="yellow"))


def display_tool_call_with_result(func_name: str, args_str: str, result: str) -> None:
    """Print a single combined panel containing the tool call and its result."""
    # Format call and result sections
    content = f"**Call:**\n```json\n{args_str}\n```\n\n---\n\n**Result:**\n```text\n{_trunc_for_display(str(result))}\n```"
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
