"""Tests for tools.edit_file — single edit API.

The edit_file tool now accepts a single edit dict rather than a list of edits.
All tests have been updated accordingly.
"""

import os
from pathlib import Path

import pytest

from harness_core.tools.edit_file import edit_file


def _unwrap(result):
    """Extract text content from an edit result (ToolResult object)."""
    return getattr(result, 'llm_text', '') + getattr(result, 'display_text', '')


class TestEditFileSafety:
    """Path traversal guard applies to edits too."""

    def test_traversal_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = edit_file("../etc/passwd", {"old_text": "x", "new_text": "y"})
            content = _unwrap(result)
            assert "traversal" in content.lower() or "Error" in content
        finally:
            os.chdir(old_cwd)

    def test_missing_edit_dict_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello")
            # Pass an empty dict – should be rejected
            result = edit_file(str(target), {})
            content = _unwrap(result)
            assert "invalid" in content.lower() or "Error" in content
        finally:
            os.chdir(old_cwd)


class TestEditFileErrors:
    """Failure modes return clear error messages."""

    def test_missing_file_returns_error(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = edit_file("nope.txt", {"old_text": "x", "new_text": "y"})
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
            result = edit_file(str(target), {"old_text": "xyz_nonexistent", "new_text": "abc"})
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
            result = edit_file(str(target), {"old_text": "", "new_text": "y"})
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
            result = edit_file(str(target), {"old_text": "hello", "new_text": None})
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
            result = edit_file(str(target), {"old_text": "world", "new_text": "earth"})
            assert target.read_text() == "hello earth"
            content = _unwrap(result)
            assert "Edit #1" in content
        finally:
            os.chdir(old_cwd)

    def test_chained_edits_separate_calls(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("alpha beta gamma")
            # First edit
            result1 = edit_file(str(target), {"old_text": "beta", "new_text": "BETA"})
            assert target.read_text() == "alpha BETA gamma"
            content1 = _unwrap(result1)
            assert "Edit #1" in content1
            # Second edit
            result2 = edit_file(str(target), {"old_text": "gamma", "new_text": "GAMMA"})
            assert target.read_text() == "alpha BETA GAMMA"
            content2 = _unwrap(result2)
            assert "Edit #1" in content2
        finally:
            os.chdir(old_cwd)

    def test_later_edits_see_modifications(self, tmp_path):
        """Sequential calls see previous modifications."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("x y z")
            edit_file(str(target), {"old_text": "x y", "new_text": "X"})
            edit_file(str(target), {"old_text": "X z", "new_text": "DONE"})
            assert target.read_text() == "DONE"
        finally:
            os.chdir(old_cwd)

    def test_first_match_only(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("apple apple apple")
            result = edit_file(str(target), {"old_text": "apple", "new_text": "banana"})
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
            result = edit_file(str(target), {"old_text": "old_line_a\nold_line_b", "new_text": "new_line_x\nnew_line_y\nnew_line_z"})
            expected = "line1\nnew_line_x\nnew_line_y\nnew_line_z\nline4\n"
            assert target.read_text() == expected
        finally:
            os.chdir(old_cwd)

    def test_no_effective_change_returns_dim(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello")
            result = edit_file(str(target), {"old_text": "hello", "new_text": "hello"})
            assert target.read_text() == "hello"
        finally:
            os.chdir(old_cwd)

    def test_newline_counting_in_report(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            content = "before\nold_a\nold_b\nafter\n"
            target.write_text(content)
            result = edit_file(str(target), {"old_text": "old_a\nold_b", "new_text": "replaced"})
            content_str = _unwrap(result)
            assert "2 line(s)" in content_str
        finally:
            os.chdir(old_cwd)


class TestEditFileAtomicRollback:
    """When a single edit fails, no changes are made (atomic per call)."""

    def test_rollback_on_failure(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            original = "alpha beta gamma"
            target.write_text(original)
            # First edit succeeds
            result1 = edit_file(str(target), {"old_text": "beta", "new_text": "BETA"})
            assert target.read_text() == "alpha BETA gamma"
            # Second edit fails; file should remain as after first edit (no further change)
            result2 = edit_file(str(target), {"old_text": "nonexistent_xyz", "new_text": "X"})
            content = _unwrap(result2)
            assert "Edit #1" in content  # refers to this single edit attempt
            assert target.read_text() == "alpha BETA gamma"
        finally:
            os.chdir(old_cwd)
