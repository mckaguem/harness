"""Tests for the /tasks command."""

import sys
from unittest.mock import Mock, patch
from harness_core.commands.tasks import cmd_tasks


class TestTasksCommand:
    """Tests for the /tasks slash command handler."""

    def test_tasks_command_with_agent(self):
        """Test that /tasks displays tasks when agent has a task list."""
        # Create mock tasks
        mock_agent = Mock()
        # Set task_list to a TaskList instance (not _task_list, since we now use the public property)
        from harness_core.agent.task_list import TaskList

        # Test 1: with tasks
        task_list = TaskList()
        task_list.initialize_tasks(["Write documentation", "Fix bug"])
        # Set statuses to match test expectations
        for t in task_list.tasks:
            if t.description == "Write documentation":
                t.status = "completed"
            elif t.description == "Fix bug":
                t.status = "in_progress"
        mock_agent.task_list = task_list

        with patch("harness_core.commands.tasks.display_info") as mock_display:
            cmd_tasks("", mock_agent)

            assert mock_display.called

    def test_tasks_command_without_agent(self):
        """Test that /tasks handles missing agent gracefully."""
        with patch("harness_core.commands.tasks.display_info") as mock_display:
            cmd_tasks("", None)

            assert mock_display.called
            text = mock_display.call_args[0][0]
            assert "No active task list" in text

    def test_tasks_command_empty_list(self):
        """Test that /tasks handles empty task list."""
        from harness_core.agent.task_list import TaskList

        mock_agent = Mock()
        # Create a TaskList but don't initialize any tasks in it
        from harness_core.agent.task_list import TaskList
        mock_agent.task_list = TaskList()

        with patch("harness_core.commands.tasks.display_info") as mock_display:
            cmd_tasks("", mock_agent)

            assert mock_display.called
            text = mock_display.call_args[0][0]
            assert "No tasks have been initialized" in text
