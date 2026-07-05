"""Tests for the /tasks command."""

import sys
from unittest.mock import Mock, patch
from commands.tasks import cmd_tasks


def test_tasks_command_with_agent():
    """Test that /tasks displays tasks when agent has a task list."""
    # Create mock tasks
    mock_task1 = Mock()
    mock_task1.id = 1
    mock_task1.description = "Write documentation"
    mock_task1.status = "completed"
    
    mock_task2 = Mock()
    mock_task2.id = 2
    mock_task2.description = "Fix bug"
    mock_task2.status = "in_progress"
    
    # Use TaskList directly for realistic behavior
    from agent.task_list import TaskList
    task_list = TaskList()
    task_list.initialize_tasks(["Write documentation", "Fix bug"])
    
    # Manually set statuses to match test expectations
    for task in task_list.tasks:
        if task.description == "Write documentation":
            task.status = "completed"
        elif task.description == "Fix bug":
            task.status = "in_progress"
    
    mock_agent = Mock()
    mock_agent._task_list = task_list
    
    # Capture the display output by patching display_message_panel
    with patch("terminal_io.display.display_message_panel") as mock_display:
        cmd_tasks("", mock_agent)
        
        # Verify display was called
        assert mock_display.called
        call_args = mock_display.call_args[0]
        text = call_args[0]
        theme = call_args[1] if len(call_args) > 1 else "status"
        
        assert "Task 1" in text and "Write documentation" in text
        assert "COMPLETED" in text
        assert "IN_PROGRESS" in text or "Fix bug" in text


def test_tasks_command_without_agent():
    """Test that /tasks handles missing agent gracefully."""
    with patch("terminal_io.display.display_message_panel") as mock_display:
        cmd_tasks("", None)
        
        assert mock_display.called
        text = mock_display.call_args[0][0]
        assert "No active task list" in text


def test_tasks_command_empty_list():
    """Test that /tasks handles empty task list."""
    from agent.task_list import TaskList
    
    mock_agent = Mock()
    # Create a TaskList but don't initialize any tasks in it
    # The default TaskList has no tasks, so len(tasks) == 0
    mock_agent._task_list = TaskList()
    
    with patch("terminal_io.display.display_message_panel") as mock_display:
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
