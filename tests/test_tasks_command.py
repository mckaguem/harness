"""Tests for the /tasks command."""

import sys
from unittest.mock import Mock, MagicMock
from commands.tasks import cmd_tasks


def test_tasks_command_with_agent():
    """Test that /tasks displays tasks when agent has a task list."""
    # Create a mock agent with tasks
    mock_task1 = Mock()
    mock_task1.id = 1
    mock_task1.description = "Write documentation"
    mock_task1.status = "completed"
    
    mock_task2 = Mock()
    mock_task2.id = 2
    mock_task2.description = "Fix bug"
    mock_task2.status = "in_progress"
    
    mock_tasks_list = Mock()
    mock_tasks_list.tasks = [mock_task1, mock_task2]
    
    mock_agent = Mock()
    mock_agent._tasks = mock_tasks_list
    
    # Capture the display output by patching print_message_panel
    with Mock() as mock_display:
        import terminal_io.display
        original_display = terminal_io.display.display_message_panel
        
        def capture_display(text, theme="status", title="", result_type="text"):
            mock_display.captured_text = text
            mock_display.captured_theme = theme
            mock_display.captured_title = title
        
        terminal_io.display.display_message_panel = capture_display
        
        try:
            # Run the command
            cmd_tasks("", mock_agent)
            
            # Verify display was called with correct parameters
            assert "Task 1) Write documentation   [COMPLETED]" in mock_display.captured_text
            assert "Task 2) Fix bug   [IN_PROGRESS]" in mock_display.captured_text
            assert mock_display.captured_theme == "status"
        finally:
            # Restore original function
            terminal_io.display.display_message_panel = original_display


def test_tasks_command_without_agent():
    """Test that /tasks handles missing agent gracefully."""
    with Mock() as mock_display:
        import terminal_io.display
        original_display = terminal_io.display.display_message_panel
        
        def capture_display(text, theme="status", title="", result_type="text"):
            mock_display.captured_text = text
        
        terminal_io.display.display_message_panel = capture_display
        
        try:
            # Run without agent
            cmd_tasks("", None)
            
            assert "No active task list" in mock_display.captured_text
        finally:
            terminal_io.display.display_message_panel = original_display


def test_tasks_command_empty_list():
    """Test that /tasks handles empty task list."""
    mock_tasks_list = Mock()
    mock_tasks_list.tasks = []
    
    mock_agent = Mock()
    mock_agent._tasks = mock_tasks_list
    
    with Mock() as mock_display:
        import terminal_io.display
        original_display = terminal_io.display.display_message_panel
        
        def capture_display(text, theme="status", title="", result_type="text"):
            mock_display.captured_text = text
        
        terminal_io.display.display_message_panel = capture_display
        
        try:
            cmd_tasks("", mock_agent)
            
            assert "No tasks have been initialized" in mock_display.captured_text
        finally:
            terminal_io.display.display_message_panel = original_display


if __name__ == "__main__":
    test_tasks_command_with_agent()
    print("✓ Test 1 passed")
    
    test_tasks_command_without_agent()
    print("✓ Test 2 passed")
    
    test_tasks_command_empty_list()
    print("✓ Test 3 passed")
    
    print("\nAll tests passed!")
