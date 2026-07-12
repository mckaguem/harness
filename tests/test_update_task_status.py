"""Tests for harness_core.tools.update_task_status."""

import pytest

from harness_core.agent.task_list import TaskList
from harness_core.tools.tool_result import ToolResult
from harness_core.tools.update_task_status import update_task_status
from harness_core.agent.context import CURRENT_AGENT


class _FakeAgent:
    def __init__(self, n_tasks):
        self.task_list = TaskList()
        self.task_list.initialize_tasks([f"task-{i}" for i in range(1, n_tasks + 1)])


class TestUpdateTaskStatus:
    """update_task_status via CURRENT_AGENT context."""

    def test_set_task_completed(self, monkeypatch):
        agent = _FakeAgent(2)
        monkeypatch.setattr(
            "harness_core.tools.update_task_status.CURRENT_AGENT",
            type("_Ctx", (), {"get": staticmethod(lambda: agent)})(),
        )

        result = update_task_status(1, "completed")

        assert isinstance(result, ToolResult)
        assert agent.task_list.tasks[0].status == "completed"
        assert "updated" in result.llm_text.lower()

    def test_last_task_completion_resets_list(self, monkeypatch):
        agent = _FakeAgent(1)
        monkeypatch.setattr(
            "harness_core.tools.update_task_status.CURRENT_AGENT",
            type("_Ctx", (), {"get": staticmethod(lambda: agent)})(),
        )

        result = update_task_status(1, "completed")

        assert isinstance(result, ToolResult)
        # All tasks complete -> list cleared and a completion message returned.
        assert agent.task_list.tasks == []
        assert "complete" in result.llm_text.lower()

    def test_unknown_status_returns_error(self, monkeypatch):
        agent = _FakeAgent(1)
        monkeypatch.setattr(
            "harness_core.tools.update_task_status.CURRENT_AGENT",
            type("_Ctx", (), {"get": staticmethod(lambda: agent)})(),
        )

        result = update_task_status(1, "not_a_real_status")

        assert isinstance(result, ToolResult)
        assert result.theme == "error"

    def test_no_agent_context_returns_error(self, monkeypatch):
        monkeypatch.setattr(
            "harness_core.tools.update_task_status.CURRENT_AGENT",
            type("_Ctx", (), {"get": staticmethod(lambda: None)})(),
        )
        CURRENT_AGENT.set(None)

        result = update_task_status(1, "completed")

        assert isinstance(result, ToolResult)
        assert result.theme == "error"
