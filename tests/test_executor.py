"""Tests for agent/executor.py — ToolExecutor class."""

from unittest.mock import patch, MagicMock

import pytest

from agent.executor import ToolExecutor
from tools.tool_result import ToolResult


# ── execute() ───────────────────────────────────────────────────────────


class TestToolExecutorExecute:
    """Tests for `ToolExecutor.execute()` — dispatching tool calls."""

    def test_successful_dispatch(self):
        mock_result = ToolResult(llm_text="ok", display_text="ok")
        
        with patch("tools.dispatcher.dispatch", return_value=mock_result) as mock_dispatch:
            executor = ToolExecutor(agent_name="test-agent")
            result = executor.execute("echo_tool", {"message": "hello"})

            mock_dispatch.assert_called_once_with("echo_tool", {"message": "hello"})
            assert result == mock_result

    def test_unknown_tool_raises_keyerror(self):
        with patch("tools.dispatcher.dispatch", side_effect=KeyError("tool not registered")):
            executor = ToolExecutor()
            
            with pytest.raises(KeyError, match="tool not registered"):
                executor.execute("nonexistent_tool", {})

    def test_execute_passes_args_correctly(self):
        mock_result = ToolResult(llm_text="", display_text="")
        
        with patch("tools.dispatcher.dispatch", return_value=mock_result) as mock_dispatch:
            executor = ToolExecutor()
            args = {"file_path": "/tmp/test.txt", "content": "test content"}
            
            result = executor.execute("write_file", args)

            mock_dispatch.assert_called_once_with("write_file", args)


# ── make_error_result() ─────────────────────────────────────────────────


class TestMakeErrorResult:
    """Tests for `ToolExecutor.make_error_result()` — error result creation."""

    def test_basic_error_result(self):
        executor = ToolExecutor()
        result = executor.make_error_result("test_tool", "Something went wrong")

        assert isinstance(result, ToolResult)
        assert result.llm_text == "Something went wrong"
        assert result.display_text == "Something went wrong"
        assert result.type_tag == "text"
        assert result.title == "Error: test_tool"
        assert result.theme == "error"

    def test_error_result_with_special_characters(self):
        executor = ToolExecutor()
        error_msg = "File not found: /path/with/special/chars.txt\nLine 42"
        
        result = executor.make_error_result("read_file", error_msg)

        assert error_msg in result.llm_text
        assert error_msg in result.display_text

    def test_error_result_different_tool_names(self):
        executor = ToolExecutor()
        
        for tool_name in ["execute_bash", "edit_file", "grep"]:
            result = executor.make_error_result(tool_name, f"Failed: {tool_name}")
            assert result.title == f"Error: {tool_name}"
            assert result.theme == "error"


# ── make_submit_results_block() ────────────────────────────────────────


class TestMakeSubmitResultsBlock:
    """Tests for `ToolExecutor.make_submit_results_block()` — blocking logic."""

    def test_no_incomplete_tasks_returns_none(self):
        executor = ToolExecutor()
        result = executor.make_submit_results_block(has_incomplete_tasks=False)
        assert result is None

    def test_with_incomplete_tasks_returns_dict(self):
        executor = ToolExecutor()
        result = executor.make_submit_results_block(has_incomplete_tasks=True)

        assert isinstance(result, dict)
        assert "role" in result
        assert "content" in result
        assert "result" in result
        assert result["role"] == "user"

    def testblocked_message_content(self):
        executor = ToolExecutor()
        result = executor.make_submit_results_block(has_incomplete_tasks=True)

        content = result["content"]
        assert "SYSTEM ERROR" in content
        assert "incomplete tasks" in content.lower()
        assert "submit_results" in content

    def test_blocked_result_is_tool_result(self):
        executor = ToolExecutor()
        result = executor.make_submit_results_block(has_incomplete_tasks=True)

        tool_result = result["result"]
        assert isinstance(tool_result, ToolResult)
        assert tool_result.theme == "error"
        assert tool_result.title == "Error: submit_results"


# ── Initialization ─────────────────────────────────────────────────────


class TestToolExecutorInit:
    """Tests for `ToolExecutor.__init__()` — initialization."""

    def test_default_agent_name(self):
        executor = ToolExecutor()
        assert executor._agent_name == ""

    def test_custom_agent_name(self):
        executor = ToolExecutor(agent_name="my-agent")
        assert executor._agent_name == "my-agent"
