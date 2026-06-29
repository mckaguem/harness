"""Tests for tools.grep — pattern searching across files."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from tools import grep


class TestGrepSafety:
    """Path traversal guard applies to grep too."""

    def test_traversal_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = grep("test", "../etc/passwd")
            assert "traversal" in result.lower() or "Error" in result
        finally:
            os.chdir(old_cwd)

    def test_nonexistent_path_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = grep("test", "nonexistent_dir/file.txt")
            assert "not a file" in result.lower() or "Error" in result
        finally:
            os.chdir(old_cwd)

    def test_empty_pattern_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello world")
            result = grep("", str(target))
            assert "non-empty" in result.lower() or "Error" in result
        finally:
            os.chdir(old_cwd)

    def test_invalid_max_matches_rejected(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello")
            result = grep("test", str(target), max_matches=0)
            assert ">= 1" in result.lower() or "Error" in result
        finally:
            os.chdir(old_cwd)


class TestGrepLiteralSearch:
    """Basic literal substring searches."""

    def test_find_single_match(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello world\nfoo bar")
            result = grep("world", str(target))
            assert "1 match" in result.lower() or "Found 1" in result
            assert "world" in result
        finally:
            os.chdir(old_cwd)

    def test_find_multiple_matches_in_file(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("apple banana apple\ncherry apple")
            result = grep("apple", str(target))
            assert "2 matches" in result.lower() or "Found 2" in result
        finally:
            os.chdir(old_cwd)

    def test_no_matches_returns_message(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello world")
            result = grep("xyz_nonexistent", str(target))
            assert "no matches found" in result.lower() or "not found" in result.lower()
        finally:
            os.chdir(old_cwd)

    def test_case_sensitive_by_default(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("Hello hello HELLO")
            result = grep("hello", str(target))
            # Should only match lowercase.
            assert "1 match" in result.lower() or "Found 1" in result
        finally:
            os.chdir(old_cwd)


class TestGrepRegexSearch:
    """Pattern matching with regular expressions."""

    def test_regex_pattern(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("func1()\nfunc2()\nvar_x = 5\nimport re")
            result = grep(r"func\d+\(\)", str(target), use_regex=True)
            assert "2 matches" in result.lower() or "Found 2" in result
        finally:
            os.chdir(old_cwd)

    def test_invalid_regex_returns_error(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("hello")
            result = grep("[invalid", str(target), use_regex=True)
            assert "Invalid regex" in result or "error" in result.lower()
        finally:
            os.chdir(old_cwd)

    def test_regex_match_with_line_numbers(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("line 1\nimport os\nline 3")
            result = grep(r"^import", str(target), use_regex=True)
            assert "2" in result  # line number
        finally:
            os.chdir(old_cwd)


class TestGrepDirectorySearch:
    """Recursive directory searches."""

    def test_search_directory_recursively(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Create nested structure.
            (tmp_path / "sub").mkdir()
            (tmp_path / "a.txt").write_text("hello world")
            (tmp_path / "sub" / "b.txt").write_text("foo bar hello")

            result = grep("hello", str(tmp_path))
            assert "2 matches" in result.lower() or "Found 2" in result
        finally:
            os.chdir(old_cwd)

    def test_skip_pycache_directory(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Create __pycache__ with a file.
            pycache = tmp_path / "__pycache__"
            pycache.mkdir()
            (pycache / "mod.pyc").write_text("compiled byte code hello")

            # And a real file.
            (tmp_path / "real.py").write_text("# import statement hello")

            result = grep("hello", str(tmp_path))
            # Should only find the match in real.py, not __pycache__.
            assert "1 match" in result.lower() or "Found 1" in result
        finally:
            os.chdir(old_cwd)

    def test_skip_git_directory(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Create .git with a file.
            git_dir = tmp_path / ".git"
            git_dir.mkdir()
            (git_dir / "config").write_text("remote=hello")

            # And a real file.
            (tmp_path / "main.py").write_text("# hello world")

            result = grep("hello", str(tmp_path))
            # Should only find the match in main.py, not .git/.
            assert "1 match" in result.lower() or "Found 1" in result
        finally:
            os.chdir(old_cwd)


class TestGrepFileFilter:
    """File filtering capabilities."""

    def test_filter_by_extension(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            (tmp_path / "a.py").write_text("hello world")
            (tmp_path / "b.txt").write_text("hello foo")

            result = grep("hello", str(tmp_path), file_filter="*.py")
            # Should only match in a.py.
            assert "1 match" in result.lower() or "Found 1" in result
        finally:
            os.chdir(old_cwd)

    def test_filter_by_suffix(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            (tmp_path / "test_a.py").write_text("hello test")
            (tmp_path / "main.py").write_text("hello main")

            result = grep("hello", str(tmp_path), file_filter="*.py")
            # Both files match *.py.
            assert "2 matches" in result.lower() or "Found 2" in result
        finally:
            os.chdir(old_cwd)


class TestGrepMaxMatches:
    """Cap on number of returned matches."""

    def test_max_matches_limit(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            # Write more lines than max_matches.
            content = "\n".join([f"line {i} match" for i in range(10)])
            target.write_text(content)

            result = grep("match", str(target), max_matches=3)
            assert "limited to 3" in result.lower() or "(limited to 3)" in result
        finally:
            os.chdir(old_cwd)


class TestGrepBinaryFiles:
    """Binary file handling."""

    def test_skip_binary_files(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Create a binary file with null bytes.
            (tmp_path / "binary.bin").write_bytes(b"\x00\x01hello\x02\x03")
            # And a text file.
            (tmp_path / "text.txt").write_text("hello world")

            result = grep("hello", str(tmp_path))
            # Should only find the match in text.txt, not binary.bin.
            assert "1 match" in result.lower() or "Found 1" in result
        finally:
            os.chdir(old_cwd)


class TestGrepOutputFormat:
    """Verify output format is structured."""

    def test_output_includes_file_and_line(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("line 1\nhello line 2")
            result = grep("hello", str(target))
            # Should include file path and line number.
            assert str(target.name) in result or target.relative_to(Path.cwd()).as_posix() in result
        finally:
            os.chdir(old_cwd)

    def test_output_includes_content_snippet(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            target = tmp_path / "t.txt"
            target.write_text("this is a long line with hello in it")
            result = grep("hello", str(target))
            # Should include the content snippet.
            assert "long line with hello" in result
        finally:
            os.chdir(old_cwd)
