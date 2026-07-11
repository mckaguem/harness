"""Tests for tools.dispatcher — routing tool calls to implementations."""

import pytest


class TestDispatch:
    """Tests for the dispatch() function that routes tool names."""

    def test_dispatch_calls_valid_tool(self):
        """dispatch should call the correct tool implementation."""
        from harness_core.tools.dispatcher import dispatch

        # Call execute_bash with a simple command
        result = dispatch("execute_bash", {"command": "echo hello"})
        assert hasattr(result, 'llm_text') or hasattr(result, 'display_text')
        content = getattr(result, 'llm_text', str(result)) + getattr(result, 'display_text', '')
        assert "hello" in content

    def test_dispatch_raises_keyerror_for_unknown_tool(self):
        """dispatch should raise KeyError when tool name is not registered."""
        from harness_core.tools.dispatcher import dispatch

        with pytest.raises(KeyError):
            dispatch("nonexistent_tool", {})

    def test_dispatch_returns_string_from_tool(self):
        """dispatch should return a ToolResult from the called tool."""
        from harness_core.tools.dispatcher import dispatch

        # write_file returns a ToolResult with JSON status
        with open("test_dispatcher.txt", "w") as f:
            pass  # ensure file exists but is empty

        try:
            result = dispatch("write_file", {
                "filename": "test_dispatcher.txt",
                "content": "test content"
            })
            assert hasattr(result, 'llm_text') or hasattr(result, 'display_text')
            text = getattr(result, 'llm_text', str(result)) + getattr(result, 'display_text', '')
            assert isinstance(text, str)
            assert '"status": "ok"' in text
        finally:
            import os
            if os.path.exists("test_dispatcher.txt"):
                os.remove("test_dispatcher.txt")

    def test_dispatch_forwards_args_correctly(self):
        """dispatch should pass kwargs from args dict to the tool function."""
        from harness_core.tools.dispatcher import dispatch

        # write_file expects filename and content parameters
        with open("test_kwargs.txt", "w") as f:
            pass  # ensure file exists

        try:
            result = dispatch("write_file", {
                "filename": "test_kwargs.txt",
                "content": "keyword args test"
            })
            assert hasattr(result, 'llm_text') or hasattr(result, 'display_text')
            text = getattr(result, 'llm_text', str(result)) + getattr(result, 'display_text', '')
            assert isinstance(text, str)
        finally:
            import os
            if os.path.exists("test_kwargs.txt"):
                os.remove("test_kwargs.txt")
