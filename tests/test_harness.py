"""Tests for harness.py — build_system_prompt() and run_loop()."""

import os
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest


class TestBuildSystemPrompt:
    """Tests for build_system_prompt() function."""

    def test_returns_string(self):
        from harness import build_system_prompt
        result = build_system_prompt()
        assert isinstance(result, str)

    def test_includes_base_prompt_content(self):
        """build_system_prompt should include content from system_prompt.txt."""
        from harness import build_system_prompt
        result = build_system_prompt()
        
        # Read the base prompt file directly
        with open("system_prompt.txt", "r") as f:
            base_content = f.read()
        
        assert base_content in result

    def test_includes_cwd_listing(self):
        """build_system_prompt should include current working directory contents."""
        from harness import build_system_prompt
        result = build_system_prompt()
        
        # Should contain "Current working directory contents:" section
        assert "Current working directory contents:" in result
        
        # Should list actual files/dirs in cwd
        cwd_files = sorted([entry.name for entry in Path.cwd().iterdir()])
        for filename in cwd_files[:5]:  # Check first few files
            assert filename in result

    def test_includes_agents_md_when_exists(self):
        """build_system_prompt should append AGENTS.md if it exists."""
        from harness import build_system_prompt
        
        # Verify AGENTS.md exists (it does in this project)
        agents_path = Path.cwd() / "AGENTS.md"
        assert agents_path.exists()
        
        result = build_system_prompt()
        
        # Should contain the AGENTS.md content with markers
        assert "--- AGENTS.md ---" in result
        assert "--- end AGENTS.md ---" in result

    def test_handles_missing_agents_md_gracefully(self, tmp_path):
        """build_system_prompt should work even without AGENTS.md."""
        import shutil
        
        old_cwd = os.getcwd()
        try:
            # Copy system_prompt.txt to temp dir before changing cwd
            src = os.path.join(old_cwd, "system_prompt.txt")
            dst = str(tmp_path / "system_prompt.txt")
            shutil.copy(src, dst)
            
            # Change to tmp directory (AGENTS.md won't exist there by default)
            os.chdir(tmp_path)
            
            from harness import build_system_prompt
            
            result = build_system_prompt()
            assert isinstance(result, str)
            assert len(result) > 0
            assert "Current working directory contents:" in result
        finally:
            # Restore original cwd
            os.chdir(old_cwd)

    def test_handles_file_read_errors(self, tmp_path):
        """build_system_prompt should handle file read errors gracefully."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Create a minimal system_prompt.txt
            (tmp_path / "system_prompt.txt").write_text("Test prompt")
            
            from harness import build_system_prompt
            
            # Should not raise exception even if other files have issues
            result = build_system_prompt()
            assert isinstance(result, str)
        finally:
            os.chdir(old_cwd)


class TestRunLoop:
    """Tests for run_loop() function."""

    def test_run_loop_calls_print_system_on_start(self):
        """run_loop should print a welcome message on startup."""
        from harness import run_loop
        
        # Create mock agent and client
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        with patch("harness.print_system") as mock_print:
            # Mock prompt_user to return /exit immediately (to break loop)
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/exit"
                raise AssertionError("Should only be called once")
            
            with patch("harness.prompt_user", side_effect=side_effect):
                run_loop(mock_agent, mock_client)
            
            # Should have called print_system once
            assert mock_print.call_count == 1

    def test_run_loop_handles_exit_command(self):
        """run_loop should exit when user types /exit."""
        from harness import run_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        with patch("harness.print_system"):
            # First call returns /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/exit"
                raise AssertionError("Should only be called once")
            
            with patch("harness.prompt_user", side_effect=side_effect):
                run_loop(mock_agent, mock_client)

    def test_run_loop_handles_quit_command(self):
        """run_loop should exit when user types /quit."""
        from harness import run_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        with patch("harness.print_system"):
            # First call returns /quit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/quit"
                raise AssertionError("Should only be called once")
            
            with patch("harness.prompt_user", side_effect=side_effect):
                run_loop(mock_agent, mock_client)

    def test_run_loop_displays_agent_response(self):
        """run_loop should display agent responses."""
        from harness import run_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a response output
        mock_agent.handle_prompt.return_value = [
            ("response", "Hello world!", {"eval_count": 10})
        ]
        
        with patch("harness.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness.prompt_user", side_effect=side_effect):
                with patch("harness.display_agent_response") as mock_display:
                    run_loop(mock_agent, mock_client)
                    
                    # Should have called display_agent_response once
                    assert mock_display.call_count == 1

    def test_run_loop_displays_tool_calls(self):
        """run_loop should display tool calls."""
        from harness import run_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a tool_call output
        mock_agent.handle_prompt.return_value = [
            ("tool_call", "execute_bash", '{"command": "ls"}')
        ]
        
        with patch("harness.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness.prompt_user", side_effect=side_effect):
                with patch("harness.display_tool_call") as mock_display:
                    run_loop(mock_agent, mock_client)
                    
                    # Should have called display_tool_call once
                    assert mock_display.call_count == 1

    def test_run_loop_displays_tool_results(self):
        """run_loop should display tool results."""
        from harness import run_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a tool_result output
        mock_agent.handle_prompt.return_value = [
            ("tool_result", "execute_bash", "file1.txt\nfile2.txt")
        ]
        
        with patch("harness.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness.prompt_user", side_effect=side_effect):
                with patch("harness.display_tool_result") as mock_display:
                    run_loop(mock_agent, mock_client)
                    
                    # Should have called display_tool_result once
                    assert mock_display.call_count == 1

    def test_run_loop_displays_errors(self):
        """run_loop should display error messages."""
        from harness import run_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield an error output
        mock_agent.handle_prompt.return_value = [
            ("ERROR", "Connection timeout")
        ]
        
        with patch("harness.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness.prompt_user", side_effect=side_effect):
                with patch("harness.display_error") as mock_display:
                    run_loop(mock_agent, mock_client)
                    
                    # Should have called display_error once
                    assert mock_display.call_count == 1

    def test_run_loop_handles_multiple_outputs(self):
        """run_loop should handle multiple outputs from a single prompt."""
        from harness import run_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield mixed outputs: response + tool_call + result
        mock_agent.handle_prompt.return_value = [
            ("response", "Thinking...", {"eval_count": 5}),
            ("tool_call", "execute_bash", '{"command": "ls"}'),
            ("tool_result", "execute_bash", "file1.txt"),
        ]
        
        with patch("harness.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness.prompt_user", side_effect=side_effect):
                with patch("harness.display_agent_response") as mock_resp:
                    with patch("harness.display_tool_call") as mock_tool:
                        with patch("harness.display_tool_result") as mock_result:
                            run_loop(mock_agent, mock_client)
                            
                            # Should have called each display function once
                            assert mock_resp.call_count == 1
                            assert mock_tool.call_count == 1
                            assert mock_result.call_count == 1

    def test_run_loop_ignores_unknown_command(self):
        """run_loop should continue when encountering unknown slash commands."""
        from harness import run_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a response (not break the loop)
        mock_agent.handle_prompt.return_value = [
            ("response", "Test response", {"eval_count": 10})
        ]
        
        with patch("harness.print_system"):
            # First call: unknown command, second call: exit
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/unknown"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness.prompt_user", side_effect=side_effect):
                run_loop(mock_agent, mock_client)
