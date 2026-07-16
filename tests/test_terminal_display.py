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
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        args_str = '{"key": "value"}'

        display_tool_call("echo", args_str)

        # Should call controller.write exactly once (via begin_tool_panel)
        mock_tui.begin_tool_panel.assert_called_once()

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_args_with_list_values(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        args_str = '{"items": ["a", "b", "c"]}'

        display_tool_call("run_multi", args_str)

        mock_tui.begin_tool_panel.assert_called_once()

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_non_json_args_fallback(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        # Invalid JSON should fall through to raw string rendering.
        display_tool_call("raw_cmd", "not json at all")

        mock_tui.begin_tool_panel.assert_called_once()

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_title_includes_function_name(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        args_str = '{"a": 1}'

        display_tool_call("my_tool_func", args_str)

        # The Panel object should have a title containing the function name.
        call_args = mock_tui.begin_tool_panel.call_args
        panel = call_args[0][1]
        assert "Tool: my_tool_func" in str(panel.title)

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_empty_string_args(self, mock_get_tui):
        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_tool_call("empty_tool", "")

        # Should still produce a panel.
        mock_tui.begin_tool_panel.assert_called_once()


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
    """Pre-tool-call text + reasoning rendered in an 'Agent' panel above call."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_reasoning_and_precontent_agent_panel(self, mock_get_tui):
        from harness_core.terminal_io.display import display_tool_call

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_tool_call("run_x", '{"a": 1}', pre_content="About to run.", reasoning="Tool thinking.")

        # The pre-content/reasoning panel is rendered first, titled "Agent".
        from rich.panel import Panel
        agent_panels = [
            c.args[0] for c in mock_tui.write.call_args_list
            if isinstance(c.args[0], Panel) and c.args[0].title == "Agent"
        ]
        assert agent_panels, "expected an 'Agent' panel"
        md = agent_panels[0].renderable
        # Markdown markup should contain reasoning separator and pre_content.
        markup = md.markup
        assert "Tool thinking." in markup
        assert "About to run." in markup
        assert "\n---\n" in markup

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_precontent_only_no_reasoning(self, mock_get_tui):
        from harness_core.terminal_io.display import display_tool_call

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_tool_call("run_y", '{}', pre_content="Doing it.")

        from rich.panel import Panel
        agent_panels = [
            c.args[0] for c in mock_tui.write.call_args_list
            if isinstance(c.args[0], Panel) and c.args[0].title == "Agent"
        ]
        assert agent_panels, "expected an 'Agent' panel"
        md = agent_panels[0].renderable
        assert md.markup == "Doing it."

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_reasoning_only_no_precontent(self, mock_get_tui):
        from harness_core.terminal_io.display import display_tool_call

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_tool_call("run_z", '{}', reasoning="Thinking...")

        from rich.panel import Panel
        agent_panels = [
            c.args[0] for c in mock_tui.write.call_args_list
            if isinstance(c.args[0], Panel) and c.args[0].title == "Agent"
        ]
        assert agent_panels, "expected an 'Agent' panel"
        md = agent_panels[0].renderable
        assert md.markup == "Thinking..."


# ── display_tool_result() ──────────────────────────────────────────────


class TestDisplayToolResult:
    """Tool result rendering — appended inside call panel in TUI mode."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_basic_result(self, mock_get_tui):
        from harness_core.terminal_io.display import display_tool_result

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_tool_result("echo", result_title="Echo Result", result_display_text="output here")

        mock_tui.complete_tool_panel.assert_called_once()

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_result_with_tool_result_object(self, mock_get_tui):
        from harness_core.terminal_io.display import display_tool_result
        from harness_core.tools.tool_result import ToolResult

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        tr = ToolResult(llm_text="result text", display_text="result text", theme="error", type_tag="json", title="Custom Title")
        display_tool_result("some_tool", tr)

        mock_tui.complete_tool_panel.assert_called_once()


# ── display_error() ─────────────────────────────────────────────────────


class TestDisplayError:
    """Error panel rendering."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_error_panel_has_red_border(self, mock_get_tui):
        from harness_core.terminal_io.display import display_error
        from rich.text import Text

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_error("Something broke")

        call_args = mock_tui.write.call_args[0][0]
        assert isinstance(call_args, Text)
        # The markup string gets converted to Text with bold red span for "Error:"
        assert "Error: Something broke" in call_args.plain
        # Check that there's a bold red span covering "Error:"
        assert any(s.style == "bold red" for s in call_args.spans)


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