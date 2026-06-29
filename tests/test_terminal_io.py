"""Tests for terminal_io.py — ANSI helpers, box printing, speed formatting."""

import os
from unittest.mock import patch

import pytest

from terminal_io import (
    BOLD, DIM, GREEN, RED, RESET, BLUE, c, _format_speed,
    _safe_len, print_box,
)

from model_utils import get_context_length


# ── ANSI helpers ────────────────────────────────────────────────────────


class Test_c:
    """Tests for the `c()` text colour wrapper."""

    def test_returns_string(self):
        result = c("hello", GREEN)
        assert isinstance(result, str)

    def test_wraps_text_in_colour_codes(self):
        result = c("hi", RED)
        # Should contain both foreground and reset codes.
        assert "\033[91m" in result   # RED
        assert RESET in result
        assert "hi" in result

    def test_bold_prefix_applied_when_true(self):
        result = c("text", GREEN, bold=True)
        assert BOLD in result
        assert "text" in result

    def test_bold_not_applied_by_default(self):
        result = c("text", GREEN, bold=False)
        assert BOLD not in result

    def test_empty_text_still_wrapped(self):
        result = c("", BLUE)
        # Should still contain the colour codes even with empty text.
        assert "\033[94m" in result   # BLUE
        assert RESET in result


class Test_safe_len:
    """Tests for `_safe_len()` — length ignoring ANSI escapes."""

    def test_plain_string_length(self):
        assert _safe_len("hello") == 5

    def test_strips_ansi_codes(self):
        coloured = f"{RED}red{RESET}"
        # The visible text is just "red" (3 chars).
        assert _safe_len(coloured) == 3

    def test_multiple_ansi_segments(self):
        s = "\033[91ma\033[0m\033[92mbc\033[0m"
        # Visible: a + bc = 3 chars.
        assert _safe_len(s) == 3

    def test_empty_string(self):
        assert _safe_len("") == 0


# ── Box printing ────────────────────────────────────────────────────────


class Test_print_box:
    """Tests for `print_box()` using stdout capture."""

    @patch("builtins.print")
    def test_calls_print_with_full_box(self, mock_print):
        with patch("terminal_io.os.get_terminal_size", return_value=os.terminal_size((80, 24))):
            print_box("Title", "Content here", GREEN, width=20)

        # print_box joins all lines into one string and calls print once.
        assert mock_print.call_count == 1
        output = mock_print.call_args[0][0]
        assert "---" in output           # dashed border
        assert "Title" in output
        assert "Content here" in output

    @patch("builtins.print")
    def test_rounded_style_uses_dashes(self, mock_print):
        with patch("terminal_io.os.get_terminal_size", return_value=os.terminal_size((80, 24))):
            print_box("Title", "Hello world", GREEN, width=20, style="rounded")

        output = mock_print.call_args[0][0]
        assert "---" in output

    @patch("builtins.print")
    def test_crossed_style_uses_plus(self, mock_print):
        with patch("terminal_io.os.get_terminal_size", return_value=os.terminal_size((80, 24))):
            print_box("Title", "Hello world", GREEN, width=20, style="crossed")

        output = mock_print.call_args[0][0]
        assert "+" in output

    @patch("builtins.print")
    def test_empty_content_still_has_border(self, mock_print):
        with patch("terminal_io.os.get_terminal_size", return_value=os.terminal_size((80, 24))):
            print_box("", "", GREEN, width=10)

        output = mock_print.call_args[0][0]
        assert "---" in output


# ── Speed formatting ────────────────────────────────────────────────────


class Test_format_speed:
    """Tests for `_format_speed()` — tokens/sec display."""

    def test_empty_response_returns_empty_string(self):
        assert _format_speed({}, 0) == ""

    def test_eval_only_no_context_length(self):
        resp = {"eval_count": 10, "eval_duration": 500_000_000}
        result = _format_speed(resp, context_length=0)
        assert "10 tok" in result
        # tok/s is computed from eval_duration independently of context_length.
        assert "tok/s" in result

    def test_eval_with_context_length_shows_rate(self):
        resp = {"eval_count": 20, "eval_duration": 1_000_000_000}
        result = _format_speed(resp, context_length=4096)
        assert "20 tok" in result
        assert "tok/s" in result

    def test_prompt_eval_count_only(self):
        resp = {"prompt_eval_count": 5, "prompt_eval_duration": 200_000_000}
        result = _format_speed(resp, context_length=0)
        assert "5 in" in result

    def test_both_eval_sections_present(self):
        resp = {
            "eval_count": 100,
            "eval_duration": 2_000_000_000,
            "prompt_eval_count": 10,
            "prompt_eval_duration": 500_000_000,
        }
        result = _format_speed(resp, context_length=4096)
        assert "tok" in result and "in" in result

    def test_zero_values_ignored(self):
        resp = {"eval_count": 0, "prompt_eval_count": 0}
        assert _format_speed(resp, 1024) == ""

    def test_none_values_treated_as_zero(self):
        resp = {"eval_count": None, "prompt_eval_count": None}
        assert _format_speed(resp, 1024) == ""


# ── Context length ──────────────────────────────────────────────────────


class Test_get_context_length:
    """Tests for `get_context_length()` with a mock ollama client."""

    def test_flat_context_length_key(self):
        class FakeClient:
            def show(self, model_name):
                return {"model_info": {"context_length": 8192}}

        result = get_context_length(FakeClient(), "fake-model")
        assert result == 8192

    def test_nested_dotted_key(self):
        class FakeClient:
            def show(self, model_name):
                return {
                    "model_info": {
                        "tokenizer.ggml.context-length": 4096,
                    }
                }

        result = get_context_length(FakeClient(), "fake-model")
        assert result == 4096

    def test_nested_in_list(self):
        class FakeClient:
            def show(self, model_name):
                return {
                    "model_info": [
                        {"tokenizer.ggml.context-length": 2048},
                    ]
                }

        result = get_context_length(FakeClient(), "fake-model")
        assert result == 2048

    def test_no_matching_key_returns_default(self):
        class FakeClient:
            def show(self, model_name):
                return {"model_info": {}}

        # Falls back to a sensible default (8192) so the UI always shows ctx %.
        result = get_context_length(FakeClient(), "fake-model")
        assert result == 8192

    def test_client_exception_returns_default(self):
        class BadClient:
            def show(self, model_name):
                raise ConnectionError("offline")

        # Same fallback on complete failure.
        result = get_context_length(BadClient(), "x")
        assert result == 8192


# ── Markdown rendering ────────────────────────────────────────────────

from terminal_io import _md_inline, _render_table, _render_code_block


class TestMdInline:
    """Tests for `_md_inline()` — inline markdown transforms."""

    def test_bold(self):
        result = _md_inline("**bold text**")
        assert BOLD in result
        assert "bold text" in result
        assert RESET in result

    def test_italic(self):
        result = _md_inline("*italic text*")
        assert DIM in result
        assert "italic text" in result
        assert RESET in result

    def test_bold_and_italic(self):
        result = _md_inline("***bold and italic***")
        assert BOLD in result
        assert DIM in result
        assert "bold and italic" in result

    def test_inline_code(self):
        result = _md_inline("use `print()` here")
        assert BLUE in result
        assert BOLD in result
        assert "print()" in result
        assert RESET in result

    def test_mixed_content(self):
        text = "This is **bold** and *italic* with `code`"
        result = _md_inline(text)
        assert BOLD in result
        assert DIM in result
        assert BLUE in result
        assert "bold" in result
        assert "italic" in result
        assert "code" in result

    def test_empty_string(self):
        assert _md_inline("") == ""

    def test_no_markdown_passthrough(self):
        text = "plain text without formatting"
        result = _md_inline(text)
        assert result == text


class TestRenderTable:
    """Tests for `_render_table()` — markdown table rendering."""

    def test_basic_table_alignment(self):
        lines = [
            "| Feature          | Status    | Notes              |",
            "|--------------------|------------|---------------------|",
            "  | Bash execution   | ✅ Working | 30s timeout         |  ",
            "  | File read/write  | ✅ Working | Path safety guard   |  ",
        ]
        result = _render_table(lines, 80)
        # Should have aligned columns with separator.
        assert "Feature" in result
        assert "Status" in result
        assert "Notes" in result
        assert "|---" in result or "|-" in result  # separator line
        assert "Bash execution" in result
        assert "File read/write" in result

    def test_malformed_separator_ignored(self):
        lines = [
            "| Feature          | Status    | Notes              |",
            "|--|------------------|-----------|--------------------------------|--|",  # malformed - 5 cols!
            "  | Bash execution   | ✅ Working | 30s timeout enforced           |  ",
        ]
        result = _render_table(lines, 80)
        # Should still render correctly despite malformed separator.
        assert "Feature" in result
        assert "Bash execution" in result
        # Should not have garbled output with extra columns.
        assert result.count('|') > 3  # has multiple pipes for alignment

    def test_empty_table(self):
        lines = []
        result = _render_table(lines, 80)
        assert result == ""

    def test_header_only(self):
        lines = [
            "| Col1 | Col2 |",
            "|------|------|",
        ]
        result = _render_table(lines, 80)
        # Should render header with separator but no data rows.
        assert "Col1" in result
        assert "Col2" in result
        assert "|-" in result or "|---" in result

    def test_column_width_calculation(self):
        lines = [
            "| Short | Longer Header Name |",
            "|-------|---------------------|",
            "  | A     | B                   |  ",
        ]
        result = _render_table(lines, 80)
        # Column widths should accommodate longest content.
        assert "Short" in result
        assert "Longer Header Name" in result
        assert "A" in result
        assert "B" in result


class TestRenderCodeBlock:
    """Tests for `_render_code_block()` — fenced code block rendering."""

    def test_basic_code_block(self):
        block = "print('hello')\ndef foo():\n    pass"
        result = _render_code_block(block, "python", 80)
        assert "+-" in result      # border top/bottom
        assert "-+" in result
        assert "|" in result       # side borders
        assert "print('hello')" in result
        assert "foo" in result

    def test_code_block_with_language(self):
        block = "console.log('hi')"
        result = _render_code_block(block, "javascript", 80)
        assert "javascript" in result or "text" in result.lower()

    def test_empty_block(self):
        result = _render_code_block("", "python", 80)
        # Should still return something (at least borders).
        assert isinstance(result, str)
        assert len(result) > 0
