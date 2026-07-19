"""Tests for the /goal command and the goal_met tool."""

import pytest
from unittest.mock import Mock, patch
from harness_core.agent.task_list import TaskList
from harness_core.tools.tool_result import ToolResult
from harness_core.commands.goal import cmd_goal
from harness_core.tools.goal_met import goal_met


class TestGoalCommand:
    """Tests for ``cmd_goal`` in harness_core.commands.goal."""

    def test_goal_command_sets_goal_and_forwards(self):
        mock_agent = Mock()
        mock_agent.task_list = TaskList()
        mock_agent.goal = ""

        with patch("harness_core.commands.goal.print_system") as mock_print:
            result = cmd_goal("fix all tests", mock_agent)

        # Returns a (text, False) tuple to forward to the model.
        assert isinstance(result, tuple)
        assert result[0] == "fix all tests"
        assert result[1] is False

        # Goal was stored on the agent.
        assert mock_agent.goal == "fix all tests"

        # Confirmation printed.
        mock_print.assert_called_once()
        call_kwargs = mock_print.call_args.kwargs
        if "title" in call_kwargs:
            assert "Goal Set" in call_kwargs["title"]
        else:
            assert "Goal Set" in mock_print.call_args.args[0]

    def test_goal_command_no_agent(self):
        with patch("harness_core.commands.goal.print_system") as mock_print:
            result = cmd_goal("something", None)

        assert result is False
        mock_print.assert_called_once()
        call_kwargs = mock_print.call_args.kwargs
        if "title" in call_kwargs:
            assert "No active agent" in call_kwargs["title"] or "No active agent" in call_kwargs.get("msg", "")
        else:
            joined = " ".join(str(a) for a in mock_print.call_args.args)
            assert "No active agent" in joined

    def test_goal_command_empty_usage(self):
        mock_agent = Mock()
        mock_agent.task_list = TaskList()
        mock_agent.goal = ""

        with patch("harness_core.commands.goal.print_system") as mock_print:
            result = cmd_goal("   ", mock_agent)

        assert result is False
        # Goal must remain unchanged.
        assert mock_agent.goal == ""
        mock_print.assert_called_once()
        call_kwargs = mock_print.call_args.kwargs
        if "msg" in call_kwargs:
            assert "Usage" in call_kwargs["msg"]
        else:
            joined = " ".join(str(a) for a in mock_print.call_args.args)
            assert "Usage" in joined


class TestGoalMetTool:
    """Tests for ``goal_met`` in harness_core.tools.goal_met."""

    class _FakeAgent:
        def __init__(self, n_tasks):
            self.task_list = TaskList()
            self.task_list.initialize_tasks(
                [f"task-{i}" for i in range(1, n_tasks + 1)]
            )
            self.goal = "do the thing"

    def test_goal_met_blocks_with_incomplete_tasks(self):
        agent = self._FakeAgent(1)
        result = goal_met(agent)

        assert isinstance(result, ToolResult)
        assert result.theme == "error"
        assert "incomplete" in result.llm_text.lower()
        # Goal must NOT be cleared while tasks remain.
        assert agent.goal == "do the thing"

    def test_goal_met_clears_when_no_incomplete_tasks(self):
        agent = self._FakeAgent(1)
        agent.task_list.update_status(1, "completed")
        result = goal_met(agent)

        assert isinstance(result, ToolResult)
        assert result.theme == "status"
        assert "Goal Met" in result.title
        assert agent.goal == ""

    def test_goal_met_with_empty_task_list(self):
        agent = Mock()
        agent.task_list = TaskList()  # empty, no tasks
        agent.goal = "x"

        result = goal_met(agent)

        assert isinstance(result, ToolResult)
        assert result.theme == "status"
        assert agent.goal == ""
