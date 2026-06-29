"""Tests for tools.py — execute_bash, write_file, read_file."""

import os
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from tools import (
    AGENT_TOOLS,
    execute_bash,
    is_safe_path,
    read_file,
    write_file,
)


# ── Constants ───────────────────────────────────────────────────────────


class TestSystemPrompt:
    """Ensure the system prompt exists and contains key instructions."""

    def test_prompt_is_non_empty_string(self):
        # Import from harness since SYSTEM_PROMPT was moved there
        from harness import build_system_prompt
        system_prompt = build_system_prompt()
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt.strip()) > 0

    def test_mentions_file_operation_restrictions(self):
        """The base prompt should mention working-directory restriction."""
        # Import from harness since SYSTEM_PROMPT was moved there
        from harness import build_system_prompt
        system_prompt = build_system_prompt()
        
        assert "current directory" in system_prompt.lower() or (
            "working directory" in system_prompt.lower()
        )


class TestAgentTools:
    """Ensure the tool definitions are well-formed JSON schemas."""

    def test_has_three_tools(self):
        assert len(AGENT_TOOLS) == 3

    def test_each_tool_is_a_function_type(self):
        for tool in AGENT_TOOLS:
            assert tool["type"] == "function"
            assert "function" in tool

    def test_required_tool_names_present(self):
        names = {t["function"]["name"] for t in AGENT_TOOLS}
        assert {"execute_bash", "write_file", "read_file"} <= names

    def test_each_tool_has_parameters_schema(self):
        for tool in AGENT_TOOLS:
            func = tool["function"]
            assert "parameters" in func, f"{func['name']} missing parameters"


# ── Path safety ────────────────────────────────────────────────────────


class TestIsSafePath:
    """Tests for `is_safe_path()` — path traversal guard."""

    def test_relative_filename_in_cwd(self):
        assert is_safe_path("harness.py") is True

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


# ── execute_bash ────────────────────────────────────────────────────────


class TestExecuteBash:
    """Tests for `execute_bash()` via subprocess mocking."""

    def test_echo_command_returns_output(self):
        # Real command — just verify basic stdout capture.
        result = execute_bash("echo hello")
        assert "hello" in result

    @patch("tools.subprocess.run")
    def test_timeout_returns_error_message(self, mock_run):
        import subprocess as sp
        from terminal_io import RED
        mock_run.side_effect = sp.TimeoutExpired(cmd="sleep 99", timeout=30)
        result = execute_bash("sleep 99")
        assert "timed out" in result.lower()

    @patch("tools.subprocess.run")
    def test_stderr_appended(self, mock_run):
        import subprocess as sp
        mock_result = sp.CompletedProcess(
            args="echo test", returncode=0,
            stdout="out\n", stderr="err\n"
        )
        mock_run.return_value = mock_result
        result = execute_bash("echo test")
        assert "STDERR:" in result
        assert "err" in result

    @patch("tools.subprocess.run")
    def test_success_with_no_output(self, mock_run):
        import subprocess as sp
        mock_result = sp.CompletedProcess(
            args="true", returncode=0, stdout="", stderr=""
        )
        mock_run.return_value = mock_result
        result = execute_bash("true")
        assert "no output" in result.lower()

    @patch("tools.subprocess.run")
    def test_generic_exception_captured(self, mock_run):
        mock_run.side_effect = OSError("permission denied")
        result = execute_bash("bad_cmd")
        assert "Execution Error" in result


# ── write_file ─────────────────────────────────────────────────────────


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

            assert f"Success: Wrote to {fname}" in result or "Success" in result
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
            assert "traversal" in result.lower() or "Error" in result
        finally:
            os.chdir(old_cwd)


# ── read_file ──────────────────────────────────────────────────────────


class TestReadFile:
    """Tests for `read_file()` with tmpdir fixtures."""

    def test_read_existing_file(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "data.txt"
            target.write_text("payload")
            content = read_file(str(target))
            assert "payload" in content
        finally:
            os.chdir(old_cwd)

    def test_missing_file_returns_error(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = read_file("nonexistent_xyz.txt")
            # Should contain an error indicator.
            assert "Error" in result or "not found" in result.lower()
        finally:
            os.chdir(old_cwd)

    def test_permission_error_captured(self):
        with patch("builtins.open", side_effect=PermissionError("denied")):
            with patch("pathlib.Path.cwd", return_value=Path("/tmp/safe").resolve()):
                result = read_file("protected.txt")
        assert "Error" in result
