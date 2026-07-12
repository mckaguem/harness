"""Tests for tools.list_dir — directory tree exploration."""

import os

import pytest

from harness_core.tools.list_dir import list_dir
from harness_core.tools.list_dir import IGNORE_DIRS


def _result_text(result) -> str:
    """Extract text content from a list_dir result (ToolResult)."""
    return getattr(result, 'llm_text', '') + getattr(result, 'display_text', '')


def _result_theme(result) -> str:
    """Extract theme from a list_dir result."""
    return getattr(result, 'theme', '')


def _touch(path, data=b"hello world\n"):
    """Create a file with optional byte content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


class TestListDirBasic:
    """Basic tree rendering for a small directory."""

    def test_tree_contains_entries_and_sizes(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            _touch(tmp_path / "src" / "main.py", b"x" * 2048)
            _touch(tmp_path / "src" / "utils" / "helpers.py", b"y" * 1024)
            result = list_dir("src", max_depth=2, include_hidden=False)
            content = _result_text(result)

            assert "src/" in content
            assert "main.py" in content
            assert "helpers.py" in content
            assert "(Directory)" in content
            assert "(File -" in content

            # None of the always-ignored directories should ever appear.
            for ignored in IGNORE_DIRS:
                assert ignored not in content
        finally:
            os.chdir(old_cwd)


class TestListDirIgnoreList:
    """Hardcoded token-heavy directories are always pruned."""

    def test_ignored_dirs_absent_marker_present(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            for ignored in ("node_modules", ".git", "__pycache__", ".venv", "build"):
                _touch(tmp_path / ignored / "dummy.txt", b"noise")
            _touch(tmp_path / "marker.txt", b"real")

            result = list_dir(".", max_depth=2)
            content = _result_text(result)

            assert "node_modules" not in content
            assert ".git" not in content
            assert "__pycache__" not in content
            assert ".venv" not in content
            assert "build" not in content

            # At least one real, non-ignored entry should be listed.
            assert "marker.txt" in content
        finally:
            os.chdir(old_cwd)


class TestListDirMaxDepth:
    """Depth clamping and the max-depth marker."""

    def test_max_depth_one(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            (tmp_path / "a" / "b" / "c" / "d").mkdir(parents=True)
            _touch(tmp_path / "a" / "b" / "c" / "d" / "deep.txt", b"z")

            result = list_dir("a", max_depth=1)
            content = _result_text(result)

            assert "a/" in content
            assert "b/ (Directory - max depth reached)" in content
            # 'c'/'d' are deeper than the max depth and must not be listed
            # as directory entries (use the trailing '/' to avoid matching the
            # substring inside words like "reached").
            assert "c/" not in content
            assert "d/" not in content
        finally:
            os.chdir(old_cwd)

    def test_depth_clamped_high(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            (tmp_path / "a" / "b" / "c" / "d").mkdir(parents=True)

            result = list_dir("a", max_depth=99)
            content = _result_text(result)

            # 99 clamps to 4, deep enough for a/b/c/d, so no depth marker.
            assert "max depth reached" not in content
        finally:
            os.chdir(old_cwd)


class TestListDirHidden:
    """Hidden entries are skipped unless requested."""

    def test_hidden_skipped_by_default(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            _touch(tmp_path / "visible.txt", b"v")
            _touch(tmp_path / ".hidden.txt", b"h")

            result = list_dir(".", max_depth=1, include_hidden=False)
            content = _result_text(result)

            assert ".hidden.txt" not in content
            assert "visible.txt" in content
        finally:
            os.chdir(old_cwd)

    def test_hidden_included_when_requested(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            _touch(tmp_path / "visible.txt", b"v")
            _touch(tmp_path / ".hidden.txt", b"h")

            result = list_dir(".", max_depth=1, include_hidden=True)
            content = _result_text(result)

            assert ".hidden.txt" in content
        finally:
            os.chdir(old_cwd)


class TestListDirSafety:
    """Path traversal and non-directory targets are rejected."""

    def test_traversal_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = list_dir("../outside", max_depth=1)
            assert _result_theme(result) == "error"
        finally:
            os.chdir(old_cwd)

    def test_nonexistent_dir_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = list_dir("does_not_exist_dir", max_depth=1)
            assert _result_theme(result) == "error"
        finally:
            os.chdir(old_cwd)
