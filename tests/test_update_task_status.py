"""Tests for harness_core.tools.update_task_status."""

import pytest

from harness_core.agent.task_list import TaskList
from harness_core.tools.tool_result import ToolResult
from harness_core.tools.update_task_status import update_task_status


class _FakeAgent:
    def __init__(self, n_tasks):
        self.task_list = TaskList()
        self.task_list.initialize_tasks([f"task-{i}" for i in range(1, n_tasks + 1)])


class TestUpdateTaskStatus:
    """update_task_status with explicit agent parameter."""

    def test_set_task_completed(self):
        agent = _FakeAgent(2)
        result = update_task_status(agent, 1, "completed")

        assert isinstance(result, ToolResult)
        assert agent.task_list.tasks[0].status == "completed"
        assert "updated" in result.llm_text.lower()

    def test_last_task_completion_resets_list(self):
        agent = _FakeAgent(1)
        result = update_task_status(agent, 1, "completed")

        assert isinstance(result, ToolResult)
        # All tasks complete -> list cleared and a completion message returned.
        assert agent.task_list.tasks == []
        assert "complete" in result.llm_text.lower()

    def test_unknown_status_returns_error(self):
        agent = _FakeAgent(1)
        result = update_task_status(agent, 1, "not_a_real_status")

        assert isinstance(result, ToolResult)
        assert result.theme == "error"

    def test_invalid_task_id_returns_info(self):
        """An unknown task_id is not an error — we return remaining-task info."""
        agent = _FakeAgent(2)
        result = update_task_status(agent, 999, "completed")

        assert isinstance(result, ToolResult)
        # Invalid task id → no error, just returns the existing list.
        assert agent.task_list.tasks[0].status == "pending"

