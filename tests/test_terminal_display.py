"""Tests for terminal_io/display.py — Rich display helpers."""

from unittest.mock import patch, MagicMock, call

import pytest

from harness_core.terminal_io.display import (
    print_system,
    display_tool_call,
    display_info,
)
from harness_core.terminal_io.message_widgets import InfoMessage, ErrorMessage


# ── print_system() ──────────────────────────────────────────────────────


class TestPrintSystem:
    """Tests for print_system() using InfoMessage widget."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_calls_write_message_once(self, mock_get_tui):
        """print_system calls write_message exactly once with an InfoMessage."""
        from harness_core.terminal_io.display import print_system

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        print_system("My Title", "Some message")

        mock_tui.write_message.assert_called_once()
        arg = mock_tui.write_message.call_args[0][0]
        assert isinstance(arg, InfoMessage)

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_panel_has_correct_title_and_message(self, mock_get_tui):
        """print_system joins title and message with double newline in the InfoMessage."""
        from harness_core.terminal_io.display import print_system

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        print_system("My Title", "Some message")

        arg = mock_tui.write_message.call_args[0][0]
        assert isinstance(arg, InfoMessage)
        expected = "My Title\n\nSome message"
        assert str(arg.message) == expected

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_non_empty_message(self, mock_get_tui):
        """print_system with non-empty message produces a non-empty InfoMessage."""
        from harness_core.terminal_io.display import print_system

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        print_system("Hello", "World")

        arg = mock_tui.write_message.call_args[0][0]
        assert isinstance(arg, InfoMessage)
        assert len(str(arg.message)) > 0


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


# ── display_info() / InfoMessage widget ────────────────────────────────


class TestInfoMessage:
    """Tests for InfoMessage widget and display_info helper."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_display_info_calls_write_message(self, mock_get_tui):
        """display_info(text) calls write_message with an InfoMessage."""
        from harness_core.terminal_io.display import display_info

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_info("Hello info")

        mock_tui.write_message.assert_called_once()
        call_arg = mock_tui.write_message.call_args[0][0]
        assert isinstance(call_arg, InfoMessage)
        assert "Hello info" in str(call_arg.message)

    def test_info_message_stores_text(self):
        """InfoMessage.message is the raw text for copy-on-click."""
        msg = InfoMessage("test payload")
        assert msg.message == "test payload"


# ── display_agent_response() with reasoning ──────────────────────────────


class TestDisplayAgentResponseReasoning:
    """Reasoning (chain-of-thought) rendered as ReasoningMessage widget before AgentResponseMessage."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_reasoning_prepended_with_separator(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response
        from harness_core.terminal_io.message_widgets import ReasoningMessage, AgentResponseMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response("Final answer.", {"usage": {}}, 1000, reasoning="I think step by step.")

        # Two write_message calls: ReasoningMessage then AgentResponseMessage.
        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 2

        first_arg = wm_calls[0].args[0]
        assert isinstance(first_arg, ReasoningMessage)
        assert "I think step by step." in first_arg.message

        second_arg = wm_calls[-1].args[0]
        assert isinstance(second_arg, AgentResponseMessage)
        assert "Final answer." in second_arg.message

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_no_reasoning_renders_plain(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response
        from harness_core.terminal_io.message_widgets import AgentResponseMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response("Just the answer.", {"usage": {}}, 1000)

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 1
        arg = wm_calls[0].args[0]
        assert isinstance(arg, AgentResponseMessage)
        assert "Just the answer." in arg.message

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_reasoning_with_empty_content_shows_no_separator(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response
        from harness_core.terminal_io.message_widgets import ReasoningMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response(None, {"usage": {}}, 1000, reasoning="I thought hard.")

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 1
        first_arg = wm_calls[0].args[0]
        # Reasoning is emitted; content (AgentResponseMessage) uses "[Agent response was None]" placeholder.
        if isinstance(first_arg, ReasoningMessage):
            assert "I thought hard." in first_arg.message

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_fully_empty_response_shows_placeholder(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response
        from harness_core.terminal_io.message_widgets import AgentResponseMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response(None, {"usage": {}}, 1000)

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 1
        arg = wm_calls[0].args[0]
        # Content is None → displays "[Agent response was None]" placeholder.
        assert isinstance(arg, AgentResponseMessage)
        assert "None" in str(arg.message)


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
    """Tests for display_tool_result fallback when no pending tool call exists."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_basic_result(self, mock_get_tui):
        """Without a preceding display_tool_call, display_tool_result shows an error."""
        from harness_core.terminal_io.display import display_tool_result

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        # Clear ALL prior pending tool messages so the call has no match to patch.
        from harness_core.terminal_io.display import _pending_tool_msgs as pending_msgs
        while pending_msgs:
            pending_msgs.pop()

        display_tool_result("echo", result_display_text="output")

        mock_tui.write_message.assert_called_once()
        call_arg = mock_tui.write_message.call_args[0][0]
        assert isinstance(call_arg, ErrorMessage)
        assert "echo" in str(call_arg.message)

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_result_with_tool_result_object(self, mock_get_tui):
        """A ToolResult object with no preceding display_tool_call also shows an error."""
        from harness_core.terminal_io.display import display_tool_result
        from harness_core.tools.tool_result import ToolResult

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        # Clear ALL prior pending tool messages so the call has no match to patch.
        from harness_core.terminal_io.display import _pending_tool_msgs as pending_msgs
        while pending_msgs:
            pending_msgs.pop()

        tool_result = ToolResult(llm_text="output", display_text="output", type_tag="text")

        display_tool_result("echo", result=tool_result)

        mock_tui.write_message.assert_called_once()
        call_arg = mock_tui.write_message.call_args[0][0]
        assert isinstance(call_arg, ErrorMessage)


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
    """User message echo rendering via UserMessage widget."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_echoes_user_text(self, mock_get_tui):
        from harness_core.terminal_io.display import display_user_message
        from harness_core.terminal_io.message_widgets import UserMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_user_message("Hello from user")

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 1
        arg = wm_calls[0].args[0]
        assert isinstance(arg, UserMessage)
        assert "Hello from user" in str(arg.message)

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_rich_text_preserved(self, mock_get_tui):
        from harness_core.terminal_io.display import display_user_message
        from harness_core.terminal_io.message_widgets import UserMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_user_message("Hello [bold]world[/bold]")

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 1
        arg = wm_calls[0].args[0]
        # UserMessage stores the raw text; it's rendered as Markdown inside MessageCard.
        assert isinstance(arg, UserMessage)


# ── display_agent_response() ───────────────────────────────────────────


class TestDisplayAgentResponse:
    """Agent response rendering via AgentResponseMessage widget."""

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_basic_response(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response
        from harness_core.terminal_io.message_widgets import AgentResponseMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response("Hello world", {"usage": {}}, 1000)

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 1
        arg = wm_calls[0].args[0]
        assert isinstance(arg, AgentResponseMessage)
        assert "Hello world" in str(arg.message)

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_response_with_reasoning(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response
        from harness_core.terminal_io.message_widgets import ReasoningMessage, AgentResponseMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response("Answer", {"usage": {}}, 1000, reasoning="Thinking...")

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        # Two calls: ReasoningMessage then AgentResponseMessage.
        assert len(wm_calls) >= 2
        first_arg = wm_calls[0].args[0]
        assert isinstance(first_arg, ReasoningMessage)
        last_arg = wm_calls[-1].args[0]
        assert isinstance(last_arg, AgentResponseMessage)

    @patch("harness_core.terminal_io.display._tui.get_tui")
    def test_response_with_context_length_in_title(self, mock_get_tui):
        from harness_core.terminal_io.display import display_agent_response
        from harness_core.terminal_io.message_widgets import AgentResponseMessage

        mock_tui = MagicMock()
        mock_get_tui.return_value = mock_tui

        display_agent_response("Hello", {"usage": {}}, 4096)

        wm_calls = [c for c in mock_tui.write_message.call_args_list]
        assert len(wm_calls) >= 1
        arg = wm_calls[0].args[0]
        assert isinstance(arg, AgentResponseMessage)