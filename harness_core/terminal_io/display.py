"""High-level display helpers using Rich for rendering.

These helpers build Rich renderables (``Panel`` / ``Markdown`` / ``Syntax``)
and route them to the Textual TUI output pane via :func:`terminal_io.tui.get_tui().write`
and controller methods like ``begin_tool_panel`` / ``complete_tool_panel``.
"""

from __future__ import annotations

from textual.widgets import Static
from rich.console import RenderableType
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
import json

from .speed import format_speed
from . import tui as _tui
from .message_widgets import ReasoningMessage, AgentResponseMessage, UserMessage

# Module-level handle to the most recent tool-call panel so the corresponding
# tool result can be appended to that same panel when a textual TUI is active.
# This is the single source of truth for "where does the next result go".
_LAST_TOOL_PANEL: "dict | None" = None


def _tui_write(renderable) -> None:
    """Route a renderable to the active TUI output pane."""
    controller = _tui.get_tui()
    if isinstance(renderable, str):
        renderable = Text.from_markup(renderable)
    controller.write(renderable)
    
def print_system(title: str, message: str) -> None:
    """Print a system-level notification panel."""
    _tui_write(Panel(message, title=title, border_style="magenta"))


def display_tool_call(
    func_name: str,
    args_str: str,
    summary: str | None = None,
    *,
    pre_content: str = "",
    reasoning: str | None = None,
) -> None:
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

    title = summary if summary else f"Tool: {func_name}"

    renderable = display_message_panel(
        text=display_content,
        theme="info",
        title=title,
        result_type="markdown",
        return_renderable=True,
    )

    # If the LLM accompanied this tool call with a text message (pre_tool_content)
    # and/or reasoning, render it as a separate panel ABOVE the tool-call panel so
    # users can see what the agent was thinking/saying before invoking tools.
    # Reasoning (chain-of-thought) is prepended above a "---" separator, then the
    # pre-tool-call text. Rendered as a full Markdown panel (no 5-line truncation)
    # so longer reasoning stays visible.
    if pre_content or reasoning:
        pre_body = _combine_reasoning(reasoning, pre_content)
        pre_renderable = Panel(
            Markdown(pre_body),
            title="Agent",
            border_style=_theme_border("info"),
        )
        _tui_write(pre_renderable)

    # Remember this panel so a later display_tool_result() can append the
    # result inside the same collapsible.
    global _LAST_TOOL_PANEL
    _LAST_TOOL_PANEL = {
        "renderable": renderable,
        "title": title,
        "result": None,
    }

    controller = _tui.get_tui()
    # In the textual TUI the call is mounted inside a Collapsible whose
    # title matches this panel; the result is appended inline later via
    controller.begin_tool_panel(title, renderable)


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


def display_message_panel(text: str, theme: str = "status", title: str = "",
                          result_type: str = "text", return_renderable: bool = False) -> "RenderableType | None":
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
        return_renderable: When True, return the built ``Panel`` instead of
                writing it (used by :func:`display_tool_call` so the panel can
                be reused/extended later).

    Returns:
        The built ``Panel`` when ``return_renderable`` is True, else ``None``.
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
        panel = Panel(
            f"[red]{display_content}[/red]",
            title=panel_title,
            border_style=border_style
        )
    elif result_type == "markdown":
        # Render as actual Markdown (supports bold, code blocks, etc.) for user-friendly display.
        md_obj = Markdown(display_content)
        panel = Panel(md_obj, title=panel_title, border_style=border_style)
    else:
        # Apply Rich Syntax highlighting for the appropriate format.
        syntax = Syntax(display_content, result_type, theme="monokai")
        panel = Panel(syntax, title=panel_title, border_style=border_style)

    if return_renderable:
        return panel
    _tui_write(panel)
    return None


def display_tool_result(
    func_name: str,
    result: object | None = None,
    result_title: str | None = None,
    result_display_text: str | None = None,
    result_theme: str | None = None,
    result_type_tag: str | None = None,
) -> None:
    """Print a truncated tool-result panel with syntax highlighting.

    The result is appended inside the most recent tool-call panel
    (via the TUI's complete_tool_panel method) rather than rendered as
    a fresh standalone panel — a horizontal rule separator is drawn
    between the call and the result.

    Args:
        func_name: Name of the tool that produced the result.
        result: A ToolResult object, or None if using individual parameters.
        result_title: Title override from the ToolResult object, or None.
        result_display_text: The display text content of the ToolResult.
        result_theme: Color/theme string for rendering (e.g. "info", "error").
        result_type_tag: Type tag from the ToolResult, defaults to "text".
    """
    # Support both calling conventions:
    # 1. display_tool_result(func_name, tool_result_object)
    # 2. display_tool_result(func_name, result_title=..., result_display_text=..., ...)
    if result is not None and not isinstance(result, str) and hasattr(result, 'display_text'):
        # Called with a ToolResult object
        from harness_core.tools.tool_result import ToolResult

        tool_result: ToolResult = result  # type: ignore[assignment]
        title_override = tool_result.title or func_name
        result_panel = display_message_panel(
            text=tool_result.display_text or "",
            theme=tool_result.theme or "info",
            title=title_override,
            result_type=tool_result.type_tag or "text",
            return_renderable=True,
        )
    else:
        # Called with individual parameters
        title_override = result_title or func_name
        result_panel = display_message_panel(
            text=result_display_text or "",
            theme=result_theme or "info",
            title=title_override,
            result_type=result_type_tag or "text",
            return_renderable=True,
        )

    controller = _tui.get_tui()
    # The result is appended inline into the most recent tool-call
    # Collapsible (popped off the controller's stack), after a separator.
    controller.complete_tool_panel(result_panel)


def reset_pending_tool_panel() -> None:
    """Forget the most recently displayed tool-call panel.

    Called when an unpaired event occurs (e.g. an ``ERROR``) so a later tool
    result does not incorrectly fold into a call that has no corresponding
    result.
    """
    global _LAST_TOOL_PANEL
    _LAST_TOOL_PANEL = None


def display_error(message: str) -> None:
    """Print an error message in red."""
    _tui_write(f"[red bold]Error:[/red bold] {message}")


def display_user_message(message: str) -> None:
    """Echo the user's own typed message.
    """
    _tui.get_tui().write_message(UserMessage(message))

def _combine_reasoning(reasoning: str | None, body: str) -> str:
    """Prepend reasoning/thinking above a horizontal separator, then the body.

    Used by both the agent-response panel and the pre-tool-call "Agent" panel so
    the user sees the model's thinking followed by a clear ``---`` separator and
    then the actual response / pre-tool-call text.

    The separator is only drawn when there is real body text to separate: if the
    model returned reasoning but no separate answer content, the reasoning is
    shown on its own (no dangling ``---`` with a blank panel beneath it).
    """
    if reasoning:
        if body:
            return f"{reasoning}\n\n---\n\n{body}"
        return reasoning
    return body


def display_agent_response(content: str | None, response: dict | None = None, context_length: int = 0,
                           prompt_token_count: int | None = None, reasoning: str | None = None) -> None:
    """Display the agent's response safely.

    Parameters
    ----------
    content: str | None
        The raw text response from the agent. If ``None`` is received, it is
        treated as an empty string to avoid ``TypeError`` when constructing a
        ``Markdown`` object.
    response: dict, optional
        Additional metadata (e.g., token usage) used for speed reporting.
    context_length: int, optional
        Length of the context window used for the request.
    prompt_token_count: int | None, optional
        Number of tokens in the original prompt.
    """
    if response is None:
        response = {}
    # Guard against None content – treat as empty string.
    safe_content = content if content is not None else "[Agent response was None]"
    speed_info = format_speed(response if response is not None else {}, context_length)

    if reasoning:
        _tui.get_tui().write_message(ReasoningMessage(reasoning))
    
    _tui.get_tui().write_message(AgentResponseMessage(safe_content))

    if speed_info:
        _tui.get_tui().write_message(Static(speed_info))
        _tui.get_tui().update_sidebar_usage(speed_info)
    
def display_turn_stats(response: dict | None = None, context_length: int = 0,
                       elapsed_seconds: float | None = None) -> None:
    """Push the most recent turn's usage + elapsed time into the right sidebar.

    Only the latest stats are shown (the sidebar overwrites its stats each call).
    """
    parts = []
    speed_info = format_speed(response if response is not None else {}, context_length)
    if speed_info:
        parts.append(speed_info)
    if elapsed_seconds is not None:
        parts.append(f"[dim]⏲ {elapsed_seconds:.1f}s turn[/dim]")
    if parts:
        _tui.get_tui().update_sidebar_usage("\n".join(parts))
