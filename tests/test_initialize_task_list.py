"""Tests for harness_core.tools.initialize_task_list."""

import pytest

from harness_core.agent.task_list import TaskList
from harness_core.tools.tool_result import ToolResult
from harness_core.tools.initialize_task_list import initialize_task_list
from harness_core.agent.context import CURRENT_AGENT


class _FakeAgent:
    def __init__(self):
        self.task_list = TaskList()


class TestInitializeTaskList:
    """initialize_task_list via CURRENT_AGENT context."""

    def test_valid_list_returns_markdown_result(self, monkeypatch):
        agent = _FakeAgent()
        monkeypatch.setattr(
            "harness_core.tools.initialize_task_list.CURRENT_AGENT",
            type("_Ctx", (), {"get": staticmethod(lambda: agent)})(),
        )

        result = initialize_task_list(["a", "b", "c"])

        assert isinstance(result, ToolResult)
        assert result.type_tag == "markdown"
        # Side effect: agent's TaskList now has 3 tasks.
        assert len(agent.task_list.tasks) == 3
        assert [t.description for t in agent.task_list.tasks] == ["a", "b", "c"]

    def test_empty_list_returns_error(self, monkeypatch):
        agent = _FakeAgent()
        monkeypatch.setattr(
            "harness_core.tools.initialize_task_list.CURRENT_AGENT",
            type("_Ctx", (), {"get": staticmethod(lambda: agent)})(),
        )

        result = initialize_task_list([])

        # Returns an error ToolResult (theme="error"), not a success.
        assert isinstance(result, ToolResult)
        assert result.theme == "error"
        assert len(agent.task_list.tasks) == 0

    def test_no_agent_context_returns_error(self, monkeypatch):
        monkeypatch.setattr(
            "harness_core.tools.initialize_task_list.CURRENT_AGENT",
            type("_Ctx", (), {"get": staticmethod(lambda: None)})(),
        )
        # Also clear any ambient contextvar binding.
        CURRENT_AGENT.set(None)

        result = initialize_task_list(["x"])

        assert isinstance(result, ToolResult)
        assert result.theme == "error"
