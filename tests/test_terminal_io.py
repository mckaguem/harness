"""Tests for terminal_io.py — speed formatting."""

import os
from unittest.mock import patch

import pytest

from harness_core.terminal_io import format_speed


# ── Speed formatting ────────────────────────────────────────────────────


class TestFormatSpeed:
    """Tests for `format_speed()` — tokens/sec display."""

    def test_empty_response_returns_empty_string(self):
        assert format_speed({}, 0) == ""

    def test_eval_only_no_context_length(self):
        resp = {"eval_count": 10, "eval_duration": 500_000_000}
        result = format_speed(resp, context_length=0)
        assert "10 tok" in result
        # tok/s is computed from eval_duration independently of context_length.
        assert "tok/s" in result

    def test_eval_with_context_length_shows_rate(self):
        resp = {"eval_count": 20, "eval_duration": 1_000_000_000}
        result = format_speed(resp, context_length=4096)
        assert "20 tok" in result
        assert "tok/s" in result

    def test_prompt_eval_count_only(self):
        resp = {"prompt_eval_count": 5, "prompt_eval_duration": 200_000_000}
        result = format_speed(resp, context_length=0)
        assert "5 in" in result

    def test_both_eval_sections_present(self):
        resp = {
            "eval_count": 100,
            "eval_duration": 2_000_000_000,
            "prompt_eval_count": 10,
            "prompt_eval_duration": 500_000_000,
        }
        result = format_speed(resp, context_length=4096)
        assert "tok" in result and "in" in result

    def test_zero_values_ignored(self):
        resp = {"eval_count": 0, "prompt_eval_count": 0}
        assert format_speed(resp, 1024) == ""

    def test_none_values_treated_as_zero(self):
        resp = {"eval_count": None, "prompt_eval_count": None}
        assert format_speed(resp, 1024) == ""

