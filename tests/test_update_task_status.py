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

    def test_second_in_progress_returns_error(self):
        """Setting two tasks to in_progress simultaneously returns an error."""
        agent = _FakeAgent(3)

        # First task becomes in_progress - success
        result1 = update_task_status(agent, 1, "in_progress")
        assert isinstance(result1, ToolResult)
        assert agent.task_list.tasks[0].status == "in_progress"

        # Second task cannot become in_progress - error
        result2 = update_task_status(agent, 2, "in_progress")
        assert isinstance(result2, ToolResult)
        assert result2.theme == "error"
        assert "already in_progress" in result2.llm_text.lower() or "cannot set" in result2.llm_text.lower()

    def test_in_progress_error_lists_conflicting_tasks(self):
        """Error message includes the IDs of conflicting in_progress tasks."""
        agent = _FakeAgent(3)

        update_task_status(agent, 1, "in_progress")
        update_task_status(agent, 2, "completed")  # Different status

        result = update_task_status(agent, 3, "in_progress")
        assert isinstance(result, ToolResult)
        assert result.theme == "error"
        # Should mention task 1 as conflicting (task 2 is completed, not in_progress)
        assert "1" in result.llm_text

