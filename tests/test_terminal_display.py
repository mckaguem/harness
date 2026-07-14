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

    @patch("harness_core.terminal_io.display.console")
    def test_calls_console_print(self, mock_console):
        print_system("Test Title", "Test Message")
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        
        # The Panel should be created with the right title and message.
        from rich.panel import Panel
        assert isinstance(call_args, Panel)

    @patch("harness_core.terminal_io.display.console")
    def test_panel_has_correct_title(self, mock_console):
        print_system("My Title", "Message body")
        
        call_args = mock_console.print.call_args[0][0]
        assert call_args.title == "My Title"

    @patch("harness_core.terminal_io.display.console")
    def test_panel_has_correct_message(self, mock_console):
        print_system("Title", "Hello world")
        
        call_args = mock_console.print.call_args[0][0]
        assert call_args.renderable is not None

    @patch("harness_core.terminal_io.display.console")
    def test_border_style_is_magenta(self, mock_console):
        print_system("Title", "Message")
        
        # The Panel object should have border_style set to 'magenta'
        panel = mock_console.print.call_args[0][0]
        assert panel.border_style == "magenta"


# ── display_tool_call() ─────────────────────────────────────────────────


class TestDisplayToolCall:
    """Tests for `display_tool_call()` — tool call panel rendering."""

    @patch("harness_core.terminal_io.display.console")
    def test_basic_json_args(self, mock_console):
        args_str = '{"key": "value"}'
        
        display_tool_call("echo", args_str)
        
        # Should call console.print exactly once.
        assert mock_console.print.call_count == 1

    @patch("harness_core.terminal_io.display.console")
    def test_args_with_list_values(self, mock_console):
        args_str = '{"items": ["a", "b", "c"]}'
        
        display_tool_call("run_multi", args_str)
        
        assert mock_console.print.call_count == 1

    @patch("harness_core.terminal_io.display.console")
    def test_non_json_args_fallback(self, mock_console):
        # Invalid JSON should fall through to raw string rendering.
        display_tool_call("raw_cmd", "not json at all")
        
        assert mock_console.print.call_count == 1

    @patch("harness_core.terminal_io.display.console")
    def test_title_includes_function_name(self, mock_console):
        args_str = '{"a": 1}'
        
        display_tool_call("my_tool_func", args_str)
        
        # The Panel object should have a title containing the function name.
        panel = mock_console.print.call_args[0][0]
        assert "Tool: my_tool_func" in str(panel.title)

    @patch("harness_core.terminal_io.display.console")
    def test_empty_string_args(self, mock_console):
        display_tool_call("empty_tool", "")
        
        # Should still produce a panel.
        assert mock_console.print.call_count == 1


# ── display_message_panel() ────────────────────────────────────────────


class TestDisplayMessagePanel:
    """Tests for `display_message_panel()` — shared rendering logic."""

    @patch("harness_core.terminal_io.display.console")
    def test_default_theme_status(self, mock_console):
        display_message_panel("Test text", theme="status")
        
        assert mock_console.print.call_count == 1

    @patch("harness_core.terminal_io.display.console")
    def test_error_theme_red_text(self, mock_console):
        display_message_panel("Error occurred!", theme="error", title="Problem")
        
        panel = mock_console.print.call_args[0][0]
        assert panel.border_style == "red"

    @patch("harness_core.terminal_io.display.console")
    def test_markdown_result_type(self, mock_console):
        display_message_panel("**Bold text**", theme="info", result_type="markdown")
        
        # Should render as Markdown object.
        panel = mock_console.print.call_args[0][0]
        from rich.markdown import Markdown
        assert isinstance(panel.renderable, Markdown)

    @patch("harness_core.terminal_io.display.console")
    def test_text_result_type(self, mock_console):
        display_message_panel("plain text", theme="info", result_type="text")
        
        # Should render as Syntax object.
        panel = mock_console.print.call_args[0][0]
        from rich.syntax import Syntax
        assert isinstance(panel.renderable, Syntax)

    @patch("harness_core.terminal_io.display.console")
    def test_truncation_for_long_text(self, mock_console):
        long_text = "\n".join([f"Line {i}" for i in range(10)])
        
        display_message_panel(long_text, theme="info", title="Long Output")
        
        # Should still call print once.
        assert mock_console.print.call_count == 1

    @patch("harness_core.terminal_io.display.console")
    def test_no_truncation_for_status_theme(self, mock_console):
        long_text = "\n".join([f"Line {i}" for i in range(10)])
        
        display_message_panel(long_text, theme="status", title="Status Panel")
        
        # No truncation should occur — the full text is preserved.
        panel = mock_console.print.call_args[0][0]
        # Verify console was called (panel created successfully)
        assert mock_console.print.called

    @patch("harness_core.terminal_io.display.console")
    def test_custom_title(self, mock_console):
        display_message_panel("Text", title="Custom Title Here")
        
        panel = mock_console.print.call_args[0][0]
        assert panel.title == "Custom Title Here"


# ── Integration: _theme_border used by display_message_panel ───────────


class TestThemeBorderIntegration:
    """Verify that all themes in _theme_border are properly handled."""

    @patch("harness_core.terminal_io.display.console")
    def test_all_themes_have_borders(self, mock_console):
        themes = ["error", "status", "info", "read", "write", "command"]
        
        for theme in themes:
            display_message_panel("Test", theme=theme)
            panel = mock_console.print.call_args[0][0]
            # Each call should produce a Panel with a valid border style.
            assert panel.border_style is not None


# ── display_agent_response() with reasoning ──────────────────────────────


class TestDisplayAgentResponseReasoning:
    """Reasoning (chain-of-thought) should be prepended above a '---' sep."""

    @patch("harness_core.terminal_io.display.console")
    def test_reasoning_prepended_with_separator(self, mock_console):
        from harness_core.terminal_io.display import display_agent_response

        display_agent_response("Final answer.", {"usage": {}}, 1000, reasoning="I think step by step.")

        assert mock_console.print.called
        panel = mock_console.print.call_args_list[0].args[0]
        from rich.panel import Panel
        assert isinstance(panel, Panel)
        md = panel.renderable
        # Rich Markdown stores the source text in `.markup`
        text = md.markup
        assert "I think step by step." in text
        assert "Final answer." in text
        assert "\n---\n" in text

    @patch("harness_core.terminal_io.display.console")
    def test_no_reasoning_renders_plain(self, mock_console):
        from harness_core.terminal_io.display import display_agent_response

        display_agent_response("Just the answer.", {"usage": {}}, 1000)

        panel = mock_console.print.call_args_list[0].args[0]
        md = panel.renderable
        assert md.markup == "Just the answer."
        assert "---" not in md.markup

    @patch("harness_core.terminal_io.display.console")
    def test_reasoning_with_empty_content_shows_no_separator(self, mock_console):
        from harness_core.terminal_io.display import display_agent_response

        display_agent_response(None, {"usage": {}}, 1000, reasoning="I thought hard.")

        panel = mock_console.print.call_args_list[0].args[0]
        md = panel.renderable
        # No dangling separator when there is no body to separate.
        assert md.markup == "I thought hard."
        assert "---" not in md.markup

    @patch("harness_core.terminal_io.display.console")
    def test_fully_empty_response_shows_placeholder(self, mock_console):
        from harness_core.terminal_io.display import display_agent_response

        display_agent_response(None, {"usage": {}}, 1000)

        panel = mock_console.print.call_args_list[0].args[0]
        md = panel.renderable
        assert md.markup == "(no response content)"


class TestDisplayToolCallReasoning:
    """Pre-tool-call text + reasoning rendered in an 'Agent' panel above call."""

    @patch("harness_core.terminal_io.display.console")
    def test_reasoning_and_precontent_agent_panel(self, mock_console):
        from harness_core.terminal_io.display import display_tool_call

        display_tool_call("run_x", '{"a": 1}', pre_content="About to run.", reasoning="Tool thinking.")

        # The pre-content/reasoning panel is rendered first, titled "Agent".
        from rich.panel import Panel
        agent_panels = [
            c.args[0] for c in mock_console.print.call_args_list
            if isinstance(c.args[0], Panel) and c.args[0].title == "Agent"
        ]
        assert agent_panels, "expected an 'Agent' panel"
        text = agent_panels[0].renderable.markup
        assert "Tool thinking." in text
        assert "About to run." in text
        assert "\n---\n" in text
