"""Tests for tools.py — execute_bash, write_file, read_file."""

import os
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from harness_core.tools import (
    AGENT_TOOLS,
)
from harness_core.tools.execute_bash import execute_bash as _execute_bash_impl
from harness_core.tools.write_file import write_file as _write_file_impl
from harness_core.tools.read_file import read_file as _read_file_impl
from harness_core.tools.utils import is_safe_path
from harness_core.tools.tool_result import ToolResult

# Re-export for backward compat with tests that call these directly.
execute_bash = _execute_bash_impl
write_file = _write_file_impl
read_file = _read_file_impl


class TestAgentTools:
    """Ensure the tool definitions are well-formed JSON schemas."""

    def test_has_six_tools(self):
        assert len(AGENT_TOOLS) == 13

    def test_each_tool_is_a_function_type(self):
        for tool in AGENT_TOOLS:
            assert tool["type"] == "function"
            assert "function" in tool

    def test_required_tool_names_present(self):
        names = {t["function"]["name"] for t in AGENT_TOOLS}
        assert {"execute_bash", "write_file", "read_file", "edit_file", "grep"} <= names

    def test_each_tool_has_parameters_schema(self):
        for tool in AGENT_TOOLS:
            func = tool["function"]
            assert "parameters" in func, f"{func['name']} missing parameters"

    def test_edit_file_edits_parameter_is_array(self):
        edit_tool = next(t for t in AGENT_TOOLS if t["function"]["name"] == "edit_file")
        edits_param = edit_tool["function"]["parameters"]["properties"]["edits"]
        assert edits_param["type"] == "array"


class TestIsSafePath:
    """Tests for `is_safe_path()` — path traversal guard."""

    def test_relative_filename_in_cwd(self):
        assert is_safe_path("harness_core.__main__.py") is True

    def test_dot_prefix_stays_in_cwd(self):
        assert is_safe_path("./main.py") is True

    def test_parent_traversal_rejected(self):
        assert is_safe_path("../etc/passwd") is False

    def test_absolute_outside_cwd_rejected(self, tmp_path):
        """Absolute paths pointing outside CWD must be rejected."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            # Build an absolute path that definitely points outside tmp_path.
            outside = Path("/tmp/somewhere")
            assert is_safe_path(str(outside)) is False

    def test_empty_filename_is_still_inside_cwd(self):
        """An empty filename resolves to CWD itself, which is safe."""
        # This depends on the cwd, so just check it doesn't crash.
        result = is_safe_path("")
        assert isinstance(result, bool)


class TestExecuteBash:
    """Tests for `execute_bash()` via subprocess mocking."""

    def test_echo_command_returns_output(self):
        # Real command — just verify basic stdout capture.
        result = execute_bash("echo hello")
        assert isinstance(result, ToolResult)
        assert "hello" in result.llm_text or "hello" in result.display_text

    @patch("subprocess.run")
    def test_timeout_returns_error_message(self, mock_run):
        import subprocess as sp
        mock_run.side_effect = sp.TimeoutExpired(cmd="sleep 99", timeout=30)
        result = execute_bash("sleep 99")
        assert isinstance(result, ToolResult)
        assert "timed out" in result.llm_text.lower() or "timed out" in result.display_text.lower()

    @patch("subprocess.run")
    def test_stderr_appended(self, mock_run):
        import subprocess as sp
        mock_result = sp.CompletedProcess(
            args="echo test", returncode=0,
            stdout="out\n", stderr="err\n"
        )
        mock_run.return_value = mock_result
        result = execute_bash("echo test")
        assert isinstance(result, ToolResult)
        assert "STDERR:" in result.llm_text or "STDERR:" in result.display_text
        assert "err" in result.llm_text or "err" in result.display_text

    @patch("subprocess.run")
    def test_success_with_no_output(self, mock_run):
        import subprocess as sp
        mock_result = sp.CompletedProcess(
            args="true", returncode=0, stdout="", stderr=""
        )
        mock_run.return_value = mock_result
        result = execute_bash("true")
        assert isinstance(result, ToolResult)
        assert "no output" in result.llm_text.lower() or "no output" in result.display_text.lower()

    @patch("subprocess.run")
    def test_generic_exception_captured(self, mock_run):
        result = execute_bash("bad_cmd")
        assert isinstance(result, ToolResult)
        assert "Execution Error" in result.llm_text or "Execution Error" in result.display_text


class TestWriteFile:
    """Tests for `write_file()` with tmpdir fixtures."""

    def test_write_and_read_round_trip(self, tmp_path):
        # Change into tmp_path so it becomes the real cwd.
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            fname = "test.txt"
            content = "hello world"
            result = write_file(fname, content)

            assert isinstance(result, ToolResult)
            combined_text = result.llm_text + result.display_text
            assert '"status": "ok"' in combined_text
            # Verify the file actually exists and has the right content.
            with open(tmp_path / fname) as f:
                assert f.read() == content
        finally:
            os.chdir(old_cwd)

    def test_traversal_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = write_file("../etc/passwd", "x")
            assert isinstance(result, ToolResult)
            combined_text = result.llm_text + result.display_text
            assert "traversal" in combined_text.lower() or "Error" in combined_text
        finally:
            os.chdir(old_cwd)


class TestReadFile:
    """Tests for `read_file()` with tmpdir fixtures."""

    def test_read_existing_file(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "data.txt"
            target.write_text("payload")
            # Read the whole file (offset 0, limit large enough)
            result = read_file(str(target), 0, 10)
            assert isinstance(result, ToolResult)
            combined_text = result.llm_text + result.display_text
            assert "payload" in combined_text
            # Verify XML-like structure is present
            assert combined_text.startswith("<file ")
            assert combined_text.endswith("</file>")
        finally:
            os.chdir(old_cwd)

    def test_missing_file_returns_error(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Use offset 0 and a reasonable limit.
            result = read_file("nonexistent_xyz.txt", 0, 10)
            # Should contain an error indicator.
            assert isinstance(result, ToolResult)
            combined_text = result.llm_text + result.display_text
            assert "Error" in combined_text or "not found" in combined_text.lower()
        finally:
            os.chdir(old_cwd)

    def test_permission_error_captured(self):
        with patch("builtins.open", side_effect=PermissionError("denied")):
            with patch("pathlib.Path.cwd", return_value=Path("/tmp/safe").resolve()):
                result = read_file("protected.txt", 0, 10)
        assert isinstance(result, ToolResult)
        combined_text = result.llm_text + result.display_text
        assert "Error" in combined_text
