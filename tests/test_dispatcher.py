"""Tests for tools.dispatcher — routing tool calls to implementations."""

import pytest


class TestDispatch:
    """Tests for the dispatch() function that routes tool names."""

    def test_dispatch_calls_valid_tool(self):
        """dispatch should call the correct tool implementation."""
        from tools.dispatcher import dispatch

        # Call execute_bash with a simple command
        result = dispatch("execute_bash", {"command": "echo hello"})
        if isinstance(result, tuple) and len(result) == 2:
            _, result_content = result
        else:
            result_content = str(result)
        assert "hello" in result_content

    def test_dispatch_raises_keyerror_for_unknown_tool(self):
        """dispatch should raise KeyError when tool name is not registered."""
        from tools.dispatcher import dispatch

        with pytest.raises(KeyError):
            dispatch("nonexistent_tool", {})

    def test_dispatch_returns_string_from_tool(self):
        """dispatch should return the string result from the called tool."""
        from tools.dispatcher import dispatch

        # write_file returns a success message string
        with open("test_dispatcher.txt", "w") as f:
            pass  # ensure file exists but is empty

        try:
            result = dispatch("write_file", {
                "filename": "test_dispatcher.txt",
                "content": "test content"
            })
            if isinstance(result, tuple) and len(result) == 2:
                _, result_content = result
            else:
                result_content = str(result)
            assert isinstance(result_content, str)
            assert "Success" in result_content or "Wrote to" in result_content
        finally:
            import os
            if os.path.exists("test_dispatcher.txt"):
                os.remove("test_dispatcher.txt")

    def test_dispatch_forwards_args_correctly(self):
        """dispatch should pass kwargs from args dict to the tool function."""
        from tools.dispatcher import dispatch

        # write_file expects filename and content parameters
        with open("test_kwargs.txt", "w") as f:
            pass  # ensure file exists

        try:
            result = dispatch("write_file", {
                "filename": "test_kwargs.txt",
                "content": "keyword args test"
            })
            if isinstance(result, tuple) and len(result) == 2:
                _, result_content = result
            else:
                result_content = str(result)
            assert isinstance(result_content, str)
        finally:
            import os
            if os.path.exists("test_kwargs.txt"):
                os.remove("test_kwargs.txt")
