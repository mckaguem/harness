"""Tests for terminal_io/display.py — Rich display helpers."""

from unittest.mock import patch, MagicMock, call

import pytest

from harness_core.terminal_io.display import (
    print_system,
    display_tool_call,
    _theme_border,
    display_message_panel,
)


# ── _theme_border() ─────────────────────────────────────────────────────


class TestThemeBorder:
    """Tests for `_theme_border()` — border color mapping."""

    def test_error_theme_returns_red(self):
        assert _theme_border("error") == "red"

    def test_status_theme_returns_purple(self):
        assert _theme_border("status") == "purple"

    def test_info_theme_returns_green(self):
        assert _theme_border("info") == "green"

    def test_read_theme_returns_blue(self):
        assert _theme_border("read") == "blue"

    def test_write_theme_returns_yellow(self):
        assert _theme_border("write") == "yellow"

    def test_command_theme_returns_cyan(self):
        assert _theme_border("command") == "cyan"

    def test_unknown_theme_returns_white(self):
        assert _theme_border("unknown") == "white"

    def test_empty_string_returns_white(self):
        assert _theme_border("") == "white"


# ── print_system() ──────────────────────────────────────────────────────


class TestPrintSystem:
    """Tests for `print_system()` — system message panel rendering."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_calls_tui_write(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        print_system("Test Title", "Test Message")

        mock_tui.write.assert_called_once()
        call_args = mock_tui.write.call_args[0][0]

        # The Panel should be created with the right title and message.
        from rich.panel import Panel
        assert isinstance(call_args, Panel)

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_panel_has_correct_title(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        print_system("My Title", "Message body")

        call_args = mock_tui.write.call_args[0][0]
        assert call_args.title == "My Title"

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_panel_has_correct_message(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        print_system("Title", "Hello world")

        call_args = mock_tui.write.call_args[0][0]
        assert call_args.renderable is not None

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_border_style_is_magenta(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        print_system("Title", "Message")

        # The Panel object should have border_style set to 'magenta'
        panel = mock_tui.write.call_args[0][0]
        assert panel.border_style == "magenta"


# ── display_tool_call() ─────────────────────────────────────────────────


class TestDisplayToolCall:
    """Tests for `display_tool_call()` — tool call panel rendering."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_basic_json_args(self, mock_get_tui):
        from harness_core.terminal_io.message_widgets import ToolCallMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        args_str = '{"key": "value"}'

        display_tool_call("echo", args_str)

        # Now uses write_message (direct mount) instead of begin_tool_panel.
        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 1, f"expected at least 1 write_message call, got {len(wm_calls)}"
        last_arg = wm_calls[-1].args[0]
        assert isinstance(last_arg, ToolCallMessage), f"got {type(last_arg).__name__}"
        assert "Tool: echo" in last_arg.title

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_args_with_list_values(self, mock_get_tui):
        from harness_core.terminal_io.message_widgets import ToolCallMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        args_str = '{"items": ["a", "b", "c"]}'

        display_tool_call("run_multi", args_str)

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 1, f"expected at least 1 write_message call, got {len(wm_calls)}"
        last_arg = wm_calls[-1].args[0]
        assert isinstance(last_arg, ToolCallMessage), f"got {type(last_arg).__name__}"

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_non_json_args_fallback(self, mock_get_tui):
        from harness_core.terminal_io.message_widgets import ToolCallMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        # Invalid JSON should fall through to raw string rendering.
        display_tool_call("raw_cmd", "not json at all")

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 1, f"expected at least 1 write_message call, got {len(wm_calls)}"
        last_arg = wm_calls[-1].args[0]
        assert isinstance(last_arg, ToolCallMessage), f"got {type(last_arg).__name__}"

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_title_includes_function_name(self, mock_get_tui):
        from harness_core.terminal_io.message_widgets import ToolCallMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        args_str = '{"a": 1}'

        display_tool_call("my_tool_func", args_str)

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        last_arg = wm_calls[-1].args[0]
        assert isinstance(last_arg, ToolCallMessage), f"got {type(last_arg).__name__}"
        assert "Tool: my_tool_func" in str(last_arg.title)

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_empty_string_args(self, mock_get_tui):
        from harness_core.terminal_io.message_widgets import ToolCallMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_tool_call("empty_tool", "")

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 1, f"expected at least 1 write_message call, got {len(wm_calls)}"
        last_arg = wm_calls[-1].args[0]
        assert isinstance(last_arg, ToolCallMessage), f"got {type(last_arg).__name__}"


# ── display_message_panel() ────────────────────────────────────────────


class TestDisplayMessagePanel:
    """Tests for `display_message_panel()` — shared rendering logic."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_default_theme_status(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_message_panel("Test text", theme="status")

        mock_tui.write.assert_called_once()

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_error_theme_red_text(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_message_panel("Error occurred!", theme="error", title="Problem")

        call_args = mock_tui.write.call_args[0][0]
        assert call_args.border_style == "red"

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_markdown_result_type(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_message_panel("**Bold text**", theme="info", result_type="markdown")

        # Should render as Markdown object.
        panel = mock_tui.write.call_args[0][0]
        from rich.markdown import Markdown
        assert isinstance(panel.renderable, Markdown)

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_text_result_type(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_message_panel("plain text", theme="info", result_type="text")

        # Should render as Syntax object.
        panel = mock_tui.write.call_args[0][0]
        from rich.syntax import Syntax
        assert isinstance(panel.renderable, Syntax)

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_truncation_for_long_text(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        long_text = "\n".join([f"Line {i}" for i in range(10)])

        display_message_panel(long_text, theme="info", title="Long Output")

        # Should still call write once.
        assert mock_tui.write.call_count == 1

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_no_truncation_for_status_theme(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        long_text = "\n".join([f"Line {i}" for i in range(10)])

        display_message_panel(long_text, theme="status", title="Status Panel")

        # No truncation should occur — the full text is preserved.
        panel = mock_tui.write.call_args[0][0]
        # Verify tui was called (panel created successfully)
        assert mock_tui.write.called

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_custom_title(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_message_panel("Text", title="Custom Title Here")

        panel = mock_tui.write.call_args[0][0]
        assert panel.title == "Custom Title Here"


# ── Integration: _theme_border used by display_message_panel ───────────


class TestThemeBorderIntegration:
    """Verify that all themes in _theme_border are properly handled."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_all_themes_have_borders(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        themes = ["error", "status", "info", "read", "write", "command"]

        for theme in themes:
            display_message_panel("Test", theme=theme)
            panel = mock_tui.write.call_args[0][0]
            # Each call should produce a Panel with a valid border style.
            assert panel.border_style is not None


# ── display_agent_response() with reasoning ──────────────────────────────


class TestDisplayAgentResponseReasoning:
    """Reasoning (chain-of-thought) should be prepended above a '---' sep."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_reasoning_prepended_with_separator(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response("Final answer.", {"usage": {}}, 1000, reasoning="I think step by step.")

        assert mock_tui.write.called
        panel = mock_tui.write.call_args_list[0].args[0]
        from rich.panel import Panel
        assert isinstance(panel, Panel)
        md = panel.renderable
        # Rich Markdown stores the source text in `.markup`
        text = md.markup
        assert "I think step by step." in text
        assert "Final answer." in text
        assert "\n---\n" in text

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_no_reasoning_renders_plain(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response("Just the answer.", {"usage": {}}, 1000)

        panel = mock_tui.write.call_args_list[0].args[0]
        md = panel.renderable
        assert md.markup == "Just the answer."
        assert "---" not in md.markup

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_reasoning_with_empty_content_shows_no_separator(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response(None, {"usage": {}}, 1000, reasoning="I thought hard.")

        panel = mock_tui.write.call_args_list[0].args[0]
        md = panel.renderable
        # No dangling separator when there is no body to separate.
        assert md.markup == "I thought hard."
        assert "---" not in md.markup

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_fully_empty_response_shows_placeholder(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response(None, {"usage": {}}, 1000)

        panel = mock_tui.write.call_args_list[0].args[0]
        md = panel.renderable
        assert md.markup == "(no response content)"


# ── display_tool_call() pre-content / reasoning panel ──────────────────


class TestDisplayToolCallReasoning:
    """Pre-tool-call text + reasoning rendered as ReasoningMessage + AgentResponseMessage widgets."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_reasoning_and_precontent_agent_panel(self, mock_get_tui):
        from harness_core.terminal_io.display import display_tool_call
        from harness_core.terminal_io.message_widgets import ReasoningMessage, AgentResponseMessage, ToolCallMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_tool_call("run_x", '{"a": 1}', pre_content="About to run.", reasoning="Tool thinking.")

        # Now: 3 write_message calls — ReasoningMessage, AgentResponseMessage, ToolCallMessage.
        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 3, f"expected at least 3 write_message calls (reasoning + agent response + tool call), got {len(wm_calls)}"
        # First call: ReasoningMessage with reasoning text.
        first_arg = wm_calls[0].args[0]
        assert isinstance(first_arg, ReasoningMessage), f"got {type(first_arg).__name__}"
        assert "Tool thinking." in first_arg.message
        # Second call: AgentResponseMessage with pre_content.
        second_arg = wm_calls[1].args[0]
        assert isinstance(second_arg, AgentResponseMessage), f"got {type(second_arg).__name__}"
        assert "About to run." in second_arg.message
        # Third call (or later): ToolCallMessage for the actual tool detail.
        last_arg = wm_calls[-1].args[0]
        assert isinstance(last_arg, ToolCallMessage), f"got {type(last_arg).__name__}"
        assert "Tool: run_x" in last_arg.title

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_precontent_only_no_reasoning(self, mock_get_tui):
        from harness_core.terminal_io.display import display_tool_call
        from harness_core.terminal_io.message_widgets import AgentResponseMessage, ToolCallMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_tool_call("run_y", '{}', pre_content="Doing it.")

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 2, f"expected at least 2 write_message calls (agent response + tool call), got {len(wm_calls)}"
        # First: AgentResponseMessage with pre_content.
        first_arg = wm_calls[0].args[0]
        assert isinstance(first_arg, AgentResponseMessage), f"got {type(first_arg).__name__}"
        assert "Doing it." in first_arg.message
        # Last: ToolCallMessage for the actual tool detail.
        last_arg = wm_calls[-1].args[0]
        assert isinstance(last_arg, ToolCallMessage), f"got {type(last_arg).__name__}"

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_reasoning_only_no_precontent(self, mock_get_tui):
        from harness_core.terminal_io.display import display_tool_call
        from harness_core.terminal_io.message_widgets import ReasoningMessage, ToolCallMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_tool_call("run_z", '{}', reasoning="Thinking...")

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 2, f"expected at least 2 write_message calls (reasoning + tool call), got {len(wm_calls)}"
        # First: ReasoningMessage with reasoning text.
        first_arg = wm_calls[0].args[0]
        assert isinstance(first_arg, ReasoningMessage), f"got {type(first_arg).__name__}"
        assert "Thinking..." in first_arg.message
        # Last: ToolCallMessage for the actual tool detail.
        last_arg = wm_calls[-1].args[0]
        assert isinstance(last_arg, ToolCallMessage), f"got {type(last_arg).__name__}"


# ── display_tool_result() ──────────────────────────────────────────────


class TestDisplayToolResult:
    """Tool result rendering — appended inside call panel in TUI mode."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_basic_result(self, mock_get_tui):
        from harness_core.terminal_io.display import display_tool_result

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        # Without a preceding display_tool_call, _LAST_TOOL_MSG is None, 
        # so we fall through to the legacy fallback path (display_message_panel + _tui_write).
        display_tool_result("echo", result_title="Echo Result", result_display_text="output here")

        # Fallback: should write via _tui_write (which calls controller.write).
        mock_tui.write.assert_called_once()

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_result_with_tool_result_object(self, mock_get_tui):
        from harness_core.terminal_io.display import display_tool_result
        from harness_core.tools.tool_result import ToolResult

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        tr = ToolResult(llm_text="result text", display_text="result text", theme="error", type_tag="json", title="Custom Title")
        display_tool_result("some_tool", tr)

        # Fallback: should write via _tui_write (which calls controller.write).
        mock_tui.write.assert_called_once()


# ── display_error() ─────────────────────────────────────────────────────


class TestDisplayError:
    """Error panel rendering via ErrorMessage widget."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_error_panel_has_red_border(self, mock_get_tui):
        from harness_core.terminal_io.display import display_error
        from harness_core.terminal_io.message_widgets import ErrorMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_error("Something broke")

        # Now uses write_message (direct mount) instead of write (which wraps in MessageCard).
        assert mock_tui.write_message.called, "display_error should call write_message"
        wm_arg = mock_tui.write_message.call_args[0][0]
        assert isinstance(wm_arg, ErrorMessage), f"got {type(wm_arg).__name__}"
        assert "Something broke" in wm_arg.message


# ── display_user_message() ─────────────────────────────────────────────


class TestDisplayUserMessage:
    """User message echo rendering."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_echoes_user_text(self, mock_get_tui):
        from harness_core.terminal_io.display import display_user_message

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_user_message("Hello from user")

        call_args = mock_tui.write.call_args[0][0]
        from rich.panel import Panel
        assert isinstance(call_args, Panel)
        # Title should indicate it's the user
        assert call_args.title == "🧑 You"

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_rich_text_renderable(self, mock_get_tui):
        from harness_core.terminal_io.display import display_user_message
        from rich.text import Text

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_user_message("Hello [bold]world[/bold]")

        call_args = mock_tui.write.call_args[0][0]
        from rich.panel import Panel
        assert isinstance(call_args, Panel)
        # The renderable should be a Text (not Markdown) so brackets are literal.
        assert isinstance(call_args.renderable, Text)


# ── display_agent_response() ───────────────────────────────────────────


class TestDisplayAgentResponse:
    """Agent response panel rendering."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_basic_response(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response("Hello world", {"usage": {}}, 1000)

        mock_tui.write.assert_called_once()

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_response_with_reasoning(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response("Answer", {"usage": {}}, 1000, reasoning="Thinking...")

        # Should write one panel combining reasoning and response
        assert mock_tui.write.call_count == 1
        panel = mock_tui.write.call_args[0][0]
        from rich.panel import Panel
        assert isinstance(panel, Panel)
        # Title should be "🤖 Agent Response"
        assert panel.title == "🤖 Agent Response"

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_response_with_context_length_in_title(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response("Hello", {"usage": {}}, 4096)

        panel = mock_tui.write.call_args[0][0]
        from rich.panel import Panel
        assert isinstance(panel, Panel)
        assert panel.title == "🤖 Agent Response"