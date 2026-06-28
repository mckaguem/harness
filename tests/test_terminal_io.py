"""Tests for terminal_io.py — ANSI helpers, box printing, speed formatting."""

import os
from unittest.mock import patch

import pytest

from terminal_io import (
    BOLD, DIM, GREEN, RED, RESET, BLUE, c, _format_speed, _get_context_length,
    _safe_len, print_box,
)


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
        # Without context_length we should not see tok/s.
        assert "tok/s" not in result

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
    """Tests for `_get_context_length()` with a mock ollama client."""

    def test_flat_context_length_key(self):
        class FakeClient:
            def show(self, model_name):
                return {"model_info": {"context_length": 8192}}

        result = _get_context_length(FakeClient(), "fake-model")
        assert result == 8192

    def test_nested_dotted_key(self):
        class FakeClient:
            def show(self, model_name):
                return {
                    "model_info": {
                        "tokenizer.ggml.context-length": 4096,
                    }
                }

        result = _get_context_length(FakeClient(), "fake-model")
        assert result == 4096

    def test_nested_in_list(self):
        class FakeClient:
            def show(self, model_name):
                return {
                    "model_info": [
                        {"tokenizer.ggml.context-length": 2048},
                    ]
                }

        result = _get_context_length(FakeClient(), "fake-model")
        assert result == 2048

    def test_no_matching_key_returns_zero(self):
        class FakeClient:
            def show(self, model_name):
                return {"model_info": {}}

        assert _get_context_length(FakeClient(), "fake-model") == 0

    def test_client_exception_returns_zero(self):
        class BadClient:
            def show(self, model_name):
                raise ConnectionError("offline")

        assert _get_context_length(BadClient(), "x") == 0
