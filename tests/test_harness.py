"""Tests for harness.py — user_loop interactive REPL."""

import os
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest


class TestRunLoop:
    """Tests for run_loop() function."""

    def _setup_event_bridge(self, monkeypatch):
        """Route emit_*_event helpers to call display_* functions directly.

        After the refactor, emit_*_event helpers publish through EventBus rather
        than calling display functions directly. In test contexts with no listener
        subscribed, publishes are silently dropped — so patch each emit helper
        to call the corresponding display function directly (which is what the
        patched display_* mocks in each test capture).
        """
        import harness_core.agent.loop as loop_mod

        monkeypatch.setattr(
            loop_mod, "_emit_agent_response_event",
            lambda agent, content, resp, ctx_len, reasoning=None: 
                loop_mod.display_agent_response(content, resp, ctx_len, reasoning=reasoning),
        )
        monkeypatch.setattr(
            loop_mod, "_emit_tool_call_event",
            lambda agent, func_name, args_str, summary=None, pre_content="", reasoning=None:
                loop_mod.display_tool_call(func_name, args_str, summary=summary,
                                           pre_content=pre_content or "", reasoning=reasoning),
        )
        monkeypatch.setattr(
            loop_mod, "_emit_tool_result_event",
            lambda agent, func_name, result_title=None, result_display_text="", 
                   result_theme="info", result_type_tag="text":
                loop_mod.display_tool_result(func_name, result_title=result_title,
                                             result_display_text=result_display_text or "",
                                             result_theme=result_theme or "info",
                                             result_type_tag=result_type_tag or "text"),
        )
        monkeypatch.setattr(
            loop_mod, "_emit_tool_error_event",
            lambda agent, description: 
                loop_mod.display_error(description or ""),
        )

    def test_run_loop_calls_print_system_on_start(self):
        """run_loop should print a welcome message on startup."""
        from harness_core.agent.loop import user_loop
        
        # Create mock agent and client
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        with patch("harness_core.agent.loop.print_system") as mock_print:
            # Mock prompt_user to return /exit immediately (to break loop)
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/exit"
                raise AssertionError("Should only be called once")
            
            with patch("harness_core.agent.loop.prompt_user", side_effect=side_effect):
                with patch("harness_core.agent.loop.display_agent_response") as mock_display:
                    user_loop(mock_agent, mock_client)

                        # /exit short-circuits the loop BEFORE any LLM turn, so handle_prompt
            # must never be invoked and no agent response is ever displayed.
            assert mock_agent.handle_prompt.call_count == 0
            assert mock_display.call_count == 0

            # Should have called print_system once
            assert mock_print.call_count == 1

    def test_run_loop_handles_exit_command(self):
        """run_loop should exit when user types /exit."""
        from harness_core.agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        with patch("harness_core.agent.loop.print_system"):
            # First call returns /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/exit"
                raise AssertionError("Should only be called once")
            
            with patch("harness_core.agent.loop.prompt_user", side_effect=side_effect):
                with patch("harness_core.agent.loop.display_agent_response") as mock_display:
                    user_loop(mock_agent, mock_client)

            # /exit short-circuits the loop BEFORE any LLM turn, so handle_prompt
            # must never be invoked and no agent response is ever displayed.
            assert mock_agent.handle_prompt.call_count == 0
            assert mock_display.call_count == 0

    def test_run_loop_handles_quit_command(self):
        """run_loop should exit when user types /quit."""
        from harness_core.agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        with patch("harness_core.agent.loop.print_system"):
            # First call returns /quit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/quit"
                raise AssertionError("Should only be called once")
            
            with patch("harness_core.agent.loop.prompt_user", side_effect=side_effect):
                with patch("harness_core.agent.loop.display_agent_response") as mock_display:
                    user_loop(mock_agent, mock_client)

            # /quit short-circuits the loop BEFORE any LLM turn, so handle_prompt
            # must never be invoked and no agent response is ever displayed.
            assert mock_agent.handle_prompt.call_count == 0
            assert mock_display.call_count == 0

    def test_run_loop_displays_agent_response(self, monkeypatch):
        """run_loop should display agent responses."""
        self._setup_event_bridge(monkeypatch)

        from harness_core.agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a response output
        mock_agent.handle_prompt.return_value = [
            ("response", "Hello world!", {"eval_count": 10}, None)
        ]
        
        with patch("harness_core.agent.loop.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness_core.agent.loop.prompt_user", side_effect=side_effect):
                with patch("harness_core.agent.loop.display_agent_response") as mock_display:
                    user_loop(mock_agent, mock_client)
                    
                    # Should have called display_agent_response once
                    assert mock_display.call_count == 1

    def test_run_loop_displays_tool_calls(self, monkeypatch):
        """run_loop should display tool calls."""
        self._setup_event_bridge(monkeypatch)

        from harness_core.agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a tool_call output (4-tuple as implementation expects).
        mock_agent.handle_prompt.return_value = [
            ("tool_call", "execute_bash", '{"command": "ls"}', None),
        ]
        
        with patch("harness_core.agent.loop.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness_core.agent.loop.prompt_user", side_effect=side_effect):
                with patch("harness_core.agent.loop.display_tool_call") as mock_display:
                    user_loop(mock_agent, mock_client)
                    
                    # Should have called display_tool_call once
                    assert mock_display.call_count == 1

    def test_run_loop_displays_tool_results(self, monkeypatch):
        """run_loop should display tool results."""
        self._setup_event_bridge(monkeypatch)

        from harness_core.agent.loop import user_loop
        from harness_core.tools.tool_result import ToolResult
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a tool_result output (4-tuple as implementation expects).
        result_obj = ToolResult(
            llm_text="file1.txt\nfile2.txt",
            display_text="file1.txt\nfile2.txt",
            type_tag="text",
            title="execute_bash",
            theme="status"
        )
        mock_agent.handle_prompt.return_value = [
            ("tool_result", "execute_bash", result_obj, None),
        ]
        
        with patch("harness_core.agent.loop.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness_core.agent.loop.prompt_user", side_effect=side_effect):
                with patch("harness_core.agent.loop.display_tool_result") as mock_display:
                    user_loop(mock_agent, mock_client)
                    
                    # Should have called display_tool_result once
                    assert mock_display.call_count == 1

    def test_run_loop_displays_errors(self, monkeypatch):
        """run_loop should display error messages."""
        self._setup_event_bridge(monkeypatch)

        from harness_core.agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield an error output
        mock_agent.handle_prompt.return_value = [
            ("error", "Connection timeout", None, None)
        ]
        
        with patch("harness_core.agent.loop.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness_core.agent.loop.prompt_user", side_effect=side_effect):
                with patch("harness_core.agent.loop.display_error") as mock_display:
                    user_loop(mock_agent, mock_client)
                    
                    # Should have called display_error once
                    assert mock_display.call_count == 1

    def test_run_loop_handles_multiple_outputs(self, monkeypatch):
        """run_loop should handle multiple outputs from a single prompt."""
        self._setup_event_bridge(monkeypatch)

        from harness_core.agent.loop import user_loop
        from harness_core.tools.tool_result import ToolResult
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield mixed outputs: response + tool_call + result.
        result_obj = ToolResult(
            llm_text="file1.txt",
            display_text="file1.txt",
            type_tag="text",
            title="execute_bash",
            theme="status"
        )
        mock_agent.handle_prompt.return_value = [
            ("response", "Thinking...", {"eval_count": 5}, None),
            ("tool_call", "execute_bash", '{"command": "ls"}', None),
            ("tool_result", "execute_bash", result_obj, None),
        ]
        
        with patch("harness_core.agent.loop.print_system"):
            # Provide normal message then /exit to break loop
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "test message"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness_core.agent.loop.prompt_user", side_effect=side_effect):
                with patch("harness_core.agent.loop.display_agent_response") as mock_resp:
                    with patch("harness_core.agent.loop.display_tool_call") as mock_tool:
                        with patch("harness_core.agent.loop.display_tool_result") as mock_result:
                            user_loop(mock_agent, mock_client)
                            
                            # Should have called each display function once
                            assert mock_resp.call_count == 1
                            assert mock_tool.call_count == 1
                            assert mock_result.call_count == 1

    def test_run_loop_ignores_unknown_command(self, monkeypatch):
        """run_loop should continue when encountering unknown slash commands."""
        self._setup_event_bridge(monkeypatch)
        from harness_core.agent.loop import user_loop
        
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        
        # Mock handle_prompt to yield a response (not break the loop)
        mock_agent.handle_prompt.return_value = [
            ("response", "Test response", {"eval_count": 10}, None)
        ]
        
        with patch("harness_core.agent.loop.print_system"):
            # First call: unknown command, second call: exit
            call_count = [0]
            
            def side_effect(*args):
                call_count[0] += 1
                if call_count[0] == 1:
                    return "/unknown"
                elif call_count[0] == 2:
                    return "/exit"
                raise AssertionError("Should only be called twice")
            
            with patch("harness_core.agent.loop.prompt_user", side_effect=side_effect):
                with patch("harness_core.agent.loop.display_agent_response") as mock_display:
                    user_loop(mock_agent, mock_client)

            # An unknown slash command is NOT a built-in command and is not a
            # recognised skill, so it falls through to the LLM: handle_prompt is
            # called exactly once, and the returned response is displayed.
            assert mock_agent.handle_prompt.call_count == 1
            assert mock_display.call_count >= 1
