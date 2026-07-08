"""Tests for terminal_io.py — speed formatting, context length."""

import os
from unittest.mock import patch

import pytest

from terminal_io import format_speed

from model_utils import get_context_length


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


# ── Context length ──────────────────────────────────────────────────────


class TestGetContextLength:
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
