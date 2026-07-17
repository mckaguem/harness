"""Tests for harness_core.tools.initialize_task_list."""

import pytest

from harness_core.agent.task_list import TaskList
from harness_core.tools.tool_result import ToolResult
from harness_core.tools.initialize_task_list import initialize_task_list


class _FakeAgent:
    def __init__(self):
        self.task_list = TaskList()


class TestInitializeTaskList:
    """initialize_task_list via explicit agent parameter."""

    def test_valid_list_returns_markdown_result(self):
        agent = _FakeAgent()
        result = initialize_task_list(agent, ["a", "b", "c"])

        assert isinstance(result, ToolResult)
        assert result.type_tag == "markdown"
        # Side effect: agent's TaskList now has 3 tasks.
        assert len(agent.task_list.tasks) == 3
        assert [t.description for t in agent.task_list.tasks] == ["a", "b", "c"]

    def test_empty_list_returns_error(self):
        agent = _FakeAgent()
        result = initialize_task_list(agent, [])

        # Returns an error ToolResult (theme="error"), not a success.
        assert isinstance(result, ToolResult)
        assert result.theme == "error"
        assert len(agent.task_list.tasks) == 0

    def test_no_agent_context_returns_error(self):
        # Pass None agent to simulate no-agent case
        result = initialize_task_list(None, ["x"])

        # Should fail because None has no task_list attribute
        assert isinstance(result, ToolResult)
        assert result.theme == "error"
