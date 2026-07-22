"""High-level display helpers using Rich for rendering.

These helpers build Rich renderables (``Panel`` / ``Markdown`` / ``Syntax``) 
for legacy fallback paths, but the primary flow now defers to specialized 
widget classes in :mod:`message_widgets` — ``ToolCallMessage`` owns both its 
tool-call args and result display, so ``display.py`` is purely wiring: create 
the widget and call ``controller.write_message(widget)``. A small list of
recently-displayed ToolCallMessages is kept so a matching tool result can be
appended inline via :func:`display_tool_result`.
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
from .message_widgets import ReasoningMessage, AgentResponseMessage, UserMessage, ToolCallMessage, ErrorMessage

# Queue of recently displayed ToolCallMessage widgets awaiting a result.
_pending_tool_msgs: list[ToolCallMessage] = []


def _tui_write(renderable) -> None:
    """Route a Rich renderable to the active TUI output pane."""
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
    """Display a tool call as a ToolCallMessage widget.

    Reasoning is emitted as a separate ReasoningMessage widget (if any).
    Pre-content is emitted as an AgentResponseMessage widget (if any).
    The tool-call detail itself is a single ToolCallMessage widget that 
    owns both its args display and the future result area — complete_tool_panel 
    in harness_tui.py no longer stitches together a merged Panel.

    Args:
        func_name: Name of the tool being invoked.
        args_str: JSON string of arguments (parsed for nicer display).
        summary: Optional override title. Falls back to ``"Tool: <name>"``.
        pre_content: Text to emit as an AgentResponseMessage BEFORE the call.
        reasoning: Chain-of-thought text emitted as a ReasoningMessage widget.
    """
    # Parse args for nicer display (unchanged logic).
    parsed = None
    try:
        parsed = json.loads(args_str)
        if isinstance(parsed, dict):
            lines: list[str] = []
            for key, value in parsed.items():
                if isinstance(value, list):
                    lines.append(f"**{key}**:")
                    for v in value:
                        lines.append(f"- {v}")
                else:
                    val_str = str(value)
                    val_str = val_str.replace("\\n", "\n").replace("\\r", "\r")
                    lines.append(f"**{key}**: {val_str}")
            display_content = "\n\n".join(lines)
        else:
            display_content = json.dumps(parsed, indent=2)
            display_content = display_content.replace("\\n", "\n").replace("\\r", "\r")
    except (json.JSONDecodeError, TypeError, ValueError):
        # Fallback: render raw string with decoded newlines.
        display_content = args_str.replace("\\n", "\n").replace("\\r", "\r")

    title = summary if summary else f"Tool: {func_name}"

    # Emit reasoning as ReasoningMessage widget (matching display_agent_response pattern).
    if reasoning:
        _tui.get_tui().write_message(ReasoningMessage(reasoning))

    agent_body = pre_content or ""
    if agent_body:
        _tui.get_tui().write_message(AgentResponseMessage(agent_body))

    # Build and mount the ToolCallMessage widget — it owns its own rendering.
    tool_call_msg = ToolCallMessage(title=title, tool_call_text=display_content, summary=summary or func_name)

    _pending_tool_msgs.append(tool_call_msg)
    # Keep only the last N pending calls to bound memory.
    if len(_pending_tool_msgs) > 32:
        del _pending_tool_msgs[:-16]

    controller = _tui.get_tui()
    controller.write_message(tool_call_msg)


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
    """Append a tool result into the most recent ToolCallMessage widget.

    The result is populated inline on the existing ToolCallMessage's 
    placeholder area via ``update_tool_result()`` rather than being stitched 
    together with a merged Panel by complete_tool_panel in harness_tui.py.

    Args:
        func_name: Name of the tool that produced the result (fallback title).
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
        from harness_core.tools.tool_result import ToolResult

        tool_result: ToolResult = result  # type: ignore[assignment]
        display_text = tool_result.display_text or ""
        type_tag = tool_result.type_tag or "text"
    else:
        display_text = result_display_text or ""
        type_tag = result_type_tag or "text"

    if _pending_tool_msgs:
        # Pop the most recent pending call; if it already has content, keep looking.
        widget = _pending_tool_msgs.pop()
        # Update result even on an existing placeholder — the widget owns rendering now.
        widget.update_tool_result(display_text, type_tag)

        controller = _tui.get_tui()
        if controller._app is not None:
            controller.scroll_output_to_bottom()
    else:
        # No matching call — fall back to standalone display_message_panel
        # (legacy path for stray results with no preceding call).
        panel = display_message_panel(
            text=display_text or "",
            theme=result_theme or "info",
            title=result_title or func_name,
            result_type=type_tag,
            return_renderable=True,
        )
        _tui_write(panel)


def reset_pending_tool_panel() -> None:
    """Drop the most recent pending ToolCallMessage so no future result will
    attach to it."""
    global _pending_tool_msgs
    if _pending_tool_msgs:
        _pending_tool_msgs.pop()


def display_error(message: str) -> None:
    """Display an error message using ErrorMessage widget."""
    _tui.get_tui().write_message(ErrorMessage(message))


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
