"""Tests for tools.edit_file — exact search-and-replace edits."""

import os
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from tools.edit_file import edit_file


def _unwrap(result):
    """Unpack a (type, content) tuple into its string payload."""
    if isinstance(result, tuple) and len(result) == 2:
        return result[1]
    return str(result)


class TestEditFileSafety:
    """Path traversal guard applies to edits too."""

    def test_traversal_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = edit_file("../etc/passwd", [{"old_text": "x", "new_text": "y"}])
            content = _unwrap(result)
            assert "traversal" in content.lower() or "Error" in content
        finally:
            os.chdir(old_cwd)

    def test_empty_edits_list_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello")
            result = edit_file(str(target), [])
            content = _unwrap(result)
            assert "non-empty" in content.lower() or "Error" in content
        finally:
            os.chdir(old_cwd)


class TestEditFileErrors:
    """Failure modes return clear error messages."""

    def test_missing_file_returns_error(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = edit_file("nope.txt", [{"old_text": "x", "new_text": "y"}])
            content = _unwrap(result)
            assert "not found" in content.lower() or "Error" in content
        finally:
            os.chdir(old_cwd)

    def test_old_text_not_found(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello world")
            result = edit_file(str(target), [{"old_text": "xyz_nonexistent", "new_text": "abc"}])
            content = _unwrap(result)
            assert "not found" in content.lower() or "Error" in content
        finally:
            os.chdir(old_cwd)

    def test_invalid_old_text_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello")
            result = edit_file(str(target), [{"old_text": "", "new_text": "y"}])
            content = _unwrap(result)
            assert "invalid" in content.lower() or "Error" in content
        finally:
            os.chdir(old_cwd)

    def test_invalid_new_text_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello")
            result = edit_file(str(target), [{"old_text": "hello", "new_text": None}])
            content = _unwrap(result)
            assert "invalid" in content.lower() or "Error" in content
        finally:
            os.chdir(old_cwd)


class TestEditFileSuccess:
    """Happy-path edits produce correct results."""

    def test_single_replacement(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello world")
            result = edit_file(str(target), [{"old_text": "world", "new_text": "earth"}])
            assert target.read_text() == "hello earth"
            content = _unwrap(result)
            assert "Edit #1" in content
        finally:
            os.chdir(old_cwd)

    def test_multiple_edits_in_one_call(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("alpha beta gamma")
            result = edit_file(str(target), [
                {"old_text": "beta", "new_text": "BETA"},
                {"old_text": "gamma", "new_text": "GAMMA"},
            ])
            assert target.read_text() == "alpha BETA GAMMA"
            content = _unwrap(result)
            assert "Edit #1" in content
            assert "Edit #2" in content
        finally:
            os.chdir(old_cwd)

    def test_later_edits_see_modifications(self, tmp_path):
        """Chained edits apply sequentially — second edit sees first's output."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("x y z")
            result = edit_file(str(target), [
                {"old_text": "x y", "new_text": "X"},       # x y → X  (content becomes "X z")
                {"old_text": "X z", "new_text": "DONE"},    # X z → DONE
            ])
            assert target.read_text() == "DONE"
        finally:
            os.chdir(old_cwd)

    def test_first_match_only(self, tmp_path):
        """Only the first occurrence of old_text is replaced."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("apple apple apple")
            result = edit_file(str(target), [{"old_text": "apple", "new_text": "banana"}])
            assert target.read_text() == "banana apple apple"
        finally:
            os.chdir(old_cwd)

    def test_multiline_replacement(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            content = "line1\nold_line_a\nold_line_b\nline4\n"
            target.write_text(content)
            result = edit_file(str(target), [{
                "old_text": "old_line_a\nold_line_b",
                "new_text": "new_line_x\nnew_line_y\nnew_line_z",
            }])
            expected = "line1\nnew_line_x\nnew_line_y\nnew_line_z\nline4\n"
            assert target.read_text() == expected
        finally:
            os.chdir(old_cwd)

    def test_no_effective_change_returns_dim(self, tmp_path):
        """If edits are no-ops the content stays and we report dim message."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello")
            # Replacing text with itself is a no-op.
            result = edit_file(str(target), [{"old_text": "hello", "new_text": "hello"}])
            assert target.read_text() == "hello"  # unchanged
        finally:
            os.chdir(old_cwd)

    def test_newline_counting_in_report(self, tmp_path):
        """Report says correct number of lines replaced."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            content = "before\nold_a\nold_b\nafter\n"
            target.write_text(content)
            result = edit_file(str(target), [{
                "old_text": "old_a\nold_b",
                "new_text": "replaced",
            }])
            # old_text has 1 newline → 2 lines replaced.
            content_str = _unwrap(result)
            assert "2 line(s)" in content_str
        finally:
            os.chdir(old_cwd)


class TestEditFileAtomicRollback:
    """An edit that fails mid-list rolls back — file is untouched."""

    def test_rollback_on_later_failure(self, tmp_path):
        """When any edit's old_text isn't found, nothing is written to disk.

        Atomicity means the agent never has to undo partial work — it gets one
        clear error and can re-read the original file before retrying with
        corrected old_text values.
        """
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            original = "alpha beta gamma"
            target.write_text(original)

            result = edit_file(str(target), [
                {"old_text": "beta", "new_text": "BETA"},    # would succeed in memory
                {"old_text": "nonexistent_xyz", "new_text": "X"},  # fails → roll back
            ])
            content = _unwrap(result)
            assert "Edit #2" in content
            # File must be untouched — atomic rollback.
            assert target.read_text() == original
        finally:
            os.chdir(old_cwd)

    def test_error_message_points_to_failing_edit(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("alpha beta gamma")
            result = edit_file(str(target), [
                {"old_text": "beta", "new_text": "BETA"},
                {"old_text": "nope", "new_text": "X"},
            ])
            content = _unwrap(result)
            assert "Edit #2" in content
        finally:
            os.chdir(old_cwd)
