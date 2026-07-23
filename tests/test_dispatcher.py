"""Tests for tools.dispatcher — routing tool calls to implementations."""

import asyncio
import pytest


class TestDispatch:
    """Tests for the dispatch() function that routes tool names."""

    def test_dispatch_calls_valid_tool(self):
        """dispatch should call the correct tool implementation."""
        from harness_core.tools.dispatcher import dispatch

        # Call execute_bash with a simple command
        result = asyncio.run(dispatch("execute_bash", {"command": "echo hello"}, None))
        assert hasattr(result, 'llm_text') or hasattr(result, 'display_text')
        content = getattr(result, 'llm_text', str(result)) + getattr(result, 'display_text', '')
        assert "hello" in content

    def test_dispatch_raises_keyerror_for_unknown_tool(self):
        """dispatch should raise KeyError when tool name is not registered."""
        from harness_core.tools.dispatcher import dispatch

        with pytest.raises(KeyError):
            asyncio.run(dispatch("nonexistent_tool", {}, None))

    def test_dispatch_returns_string_from_tool(self, tmp_path, monkeypatch):
        """dispatch should return a ToolResult from the called tool and write the file."""
        from harness_core.tools.dispatcher import dispatch

        # Run the write in an isolated temp dir so no stray files hit the repo CWD.
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "test_dispatcher.txt"
        target.write_text("")

        result = asyncio.run(dispatch("write_file", {
            "filename": str(target),
            "content": "test content"
        }, None))
        assert hasattr(result, 'llm_text') or hasattr(result, 'display_text')
        text = getattr(result, 'llm_text', str(result)) + getattr(result, 'display_text', '')
        assert isinstance(text, str)
        assert '"status": "ok"' in text

        # Side effect: the file on disk must actually contain what was written.
        assert target.exists()
        assert target.read_text() == "test content"

    def test_dispatch_forwards_args_correctly(self, tmp_path, monkeypatch):
        """dispatch should pass kwargs from args dict to the tool function and write the file."""
        from harness_core.tools.dispatcher import dispatch

        # Run the write in an isolated temp dir so no stray files hit the repo CWD.
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "test_kwargs.txt"
        target.write_text("")

        result = asyncio.run(dispatch("write_file", {
            "filename": str(target),
            "content": "keyword args test"
        }, None))
        assert hasattr(result, 'llm_text') or hasattr(result, 'display_text')
        text = getattr(result, 'llm_text', str(result)) + getattr(result, 'display_text', '')
        assert isinstance(text, str)

        # Side effect: the file on disk must actually contain what was written.
        assert target.exists()
        assert target.read_text() == "keyword args test"
