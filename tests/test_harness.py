"""Tests for harness.py — user_loop interactive REPL."""

import os
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest



class TestRunLoop:
    """Tests for run_loop() function."""

    def test_run_loop_calls_print_system_on_start(self):
        """run_loop should print a welcome message on startup."""
        from agent.loop import user_loop
        
        # Create mock agent and client
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        with patch("agent.loop.print_system") as mock_print:
            # Mock prompt_user to return /exit immediately (to break loop)
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/exit"
                raise AssertionError("Should only be called once")
            
            with patch("agent.loop.prompt_user", side_effect=side_effect):
                user_loop(mock_agent, mock_client)
            
            # Should have called print_system once
            assert mock_print.call_count == 1

    def test_run_loop_handles_exit_command(self):
        """run_loop should exit when user types /exit."""
        from agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        with patch("agent.loop.print_system"):
            # First call returns /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/exit"
                raise AssertionError("Should only be called once")
            
            with patch("agent.loop.prompt_user", side_effect=side_effect):
                user_loop(mock_agent, mock_client)

    def test_run_loop_handles_quit_command(self):
        """run_loop should exit when user types /quit."""
        from agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        with patch("agent.loop.print_system"):
            # First call returns /quit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/quit"
                raise AssertionError("Should only be called once")
            
            with patch("agent.loop.prompt_user", side_effect=side_effect):
                user_loop(mock_agent, mock_client)

    def test_run_loop_displays_agent_response(self):
        """run_loop should display agent responses."""
        from agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a response output
        mock_agent.handle_prompt.return_value = [
            ("response", "Hello world!", {"eval_count": 10})
        ]
        
        with patch("agent.loop.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("agent.loop.prompt_user", side_effect=side_effect):
                with patch("agent.loop.display_agent_response") as mock_display:
                    user_loop(mock_agent, mock_client)
                    
                    # Should have called display_agent_response once
                    assert mock_display.call_count == 1

    def test_run_loop_displays_tool_calls(self):
        """run_loop should display tool calls."""
        from agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a tool_call output
        mock_agent.handle_prompt.return_value = [
            ("tool_call", "execute_bash", '{"command": "ls"}')
        ]
        
        with patch("agent.loop.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("agent.loop.prompt_user", side_effect=side_effect):
                with patch("agent.loop.display_tool_call") as mock_display:
                    user_loop(mock_agent, mock_client)
                    
                    # Should have called display_tool_call once
                    assert mock_display.call_count == 1

    def test_run_loop_displays_tool_results(self):
        """run_loop should display tool results."""
        from agent.loop import user_loop
        from tools.tool_result import ToolResult
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a tool_result output (3-tuple with ToolResult)
        result_obj = ToolResult(
            llm_text="file1.txt\nfile2.txt",
            display_text="file1.txt\nfile2.txt",
            type_tag="text",
            title="execute_bash",
            theme="status"
        )
        mock_agent.handle_prompt.return_value = [
            ("tool_result", "execute_bash", result_obj)
        ]
        
        with patch("agent.loop.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("agent.loop.prompt_user", side_effect=side_effect):
                with patch("agent.loop.display_tool_result") as mock_display:
                    user_loop(mock_agent, mock_client)
                    
                    # Should have called display_tool_result once
                    assert mock_display.call_count == 1

    def test_run_loop_displays_errors(self):
        """run_loop should display error messages."""
        from agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield an error output
        mock_agent.handle_prompt.return_value = [
            ("error", "Connection timeout")
        ]
        
        with patch("agent.loop.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("agent.loop.prompt_user", side_effect=side_effect):
                with patch("agent.loop.display_error") as mock_display:
                    user_loop(mock_agent, mock_client)
                    
                    # Should have called display_error once
                    assert mock_display.call_count == 1

    def test_run_loop_handles_multiple_outputs(self):
        """run_loop should handle multiple outputs from a single prompt."""
        from agent.loop import user_loop
        from tools.tool_result import ToolResult
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield mixed outputs: response + tool_call + result
        result_obj = ToolResult(
            llm_text="file1.txt",
            display_text="file1.txt",
            type_tag="text",
            title="execute_bash",
            theme="status"
        )
        mock_agent.handle_prompt.return_value = [
            ("response", "Thinking...", {"eval_count": 5}),
            ("tool_call", "execute_bash", '{"command": "ls"}'),
            ("tool_result", "execute_bash", result_obj),
        ]
        
        with patch("agent.loop.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("agent.loop.prompt_user", side_effect=side_effect):
                with patch("agent.loop.display_agent_response") as mock_resp:
                    with patch("agent.loop.display_tool_call") as mock_tool:
                        with patch("agent.loop.display_tool_result") as mock_result:
                            user_loop(mock_agent, mock_client)
                            
                            # Should have called each display function once
                            assert mock_resp.call_count == 1
                            assert mock_tool.call_count == 1
                            assert mock_result.call_count == 1

    def test_run_loop_ignores_unknown_command(self):
        """run_loop should continue when encountering unknown slash commands."""
        from agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a response (not break the loop)
        mock_agent.handle_prompt.return_value = [
            ("response", "Test response", {"eval_count": 10})
        ]
        
        with patch("agent.loop.print_system"):
            # First call: unknown command, second call: exit
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/unknown"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("agent.loop.prompt_user", side_effect=side_effect):
                user_loop(mock_agent, mock_client)
