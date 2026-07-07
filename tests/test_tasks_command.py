"""Tests for the /tasks command."""

import sys
from unittest.mock import Mock, patch
from commands.tasks import cmd_tasks


def test_tasks_command_with_agent():
    """Test that /tasks displays tasks when agent has a task list."""
    # Create mock tasks
    mock_agent = Mock()
    # Set task_list to a TaskList instance (not _task_list, since we now use the public property)
    from agent.task_list import TaskList
    
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
    
    # Capture the display output by patching display_message_panel at the usage site
    with patch("commands.tasks.display_message_panel") as mock_display:
        cmd_tasks("", mock_agent)
        
        # Verify display was called
        assert mock_display.called
        call_args = mock_display.call_args[0]
        text = call_args[0]
        theme = call_args[1] if len(call_args) > 1 else "status"
        
        assert "Write documentation" in text
        assert "Fix bug" in text


def test_tasks_command_without_agent():
    """Test that /tasks handles missing agent gracefully."""
    from agent.context import CURRENT_AGENT
    CURRENT_AGENT.set(None)  # Reset context to simulate no running agent
    with patch("commands.tasks.display_message_panel") as mock_display:
        cmd_tasks("", None)
        
        assert mock_display.called
        text = mock_display.call_args[0][0]
        assert "No active task list" in text


def test_tasks_command_empty_list():
    """Test that /tasks handles empty task list."""
    from agent.task_list import TaskList
    
    mock_agent = Mock()
    # Create a TaskList but don't initialize any tasks in it
    from agent.task_list import TaskList
    mock_agent.task_list = TaskList()
    
    with patch("commands.tasks.display_message_panel") as mock_display:
        cmd_tasks("", mock_agent)
        
        assert mock_display.called
        text = mock_display.call_args[0][0]
        assert "No tasks have been initialized" in text


if __name__ == "__main__":
    test_tasks_command_with_agent()
    print("✓ Test 1 passed")
    
    test_tasks_command_without_agent()
    print("✓ Test 2 passed")
    
    test_tasks_command_empty_list()
    print("✓ Test 3 passed")
    
    print("\nAll tests passed!")
