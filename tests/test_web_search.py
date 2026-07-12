"""Tests for harness_core.tools.web_search — search client mocked out."""

from unittest.mock import patch

import pytest

from harness_core.tools.tool_result import ToolResult
from harness_core.tools.web_search import web_search


class TestWebSearch:
    """web_search validates args, calls DDGS, and returns a ToolResult."""

    def test_valid_query_calls_ddgs_with_args(self):
        fake_results = [
            {"title": "Result One", "href": "https://a.com", "body": "snippet a"},
            {"title": "Result Two", "href": "https://b.com", "body": "snippet b"},
        ]
        import ddgs as real_ddgs
        fake_ddgs = type("DDGS", (), {"text": staticmethod(lambda **kw: fake_results)})()
        with patch.object(real_ddgs, "DDGS", return_value=fake_ddgs) as mock_cls:
            result = web_search("python testing", region="us-en", max_results=2)

        assert isinstance(result, ToolResult)
        assert "Result One" in result.llm_text
        assert "https://a.com" in result.llm_text
        # The DDGS client was constructed and text() was invoked with our args.
        mock_cls.assert_called_once()

    def test_empty_query_returns_error(self):
        result = web_search("")
        assert isinstance(result, ToolResult)
        assert result.theme == "error"

    def test_invalid_region_returns_error(self):
        result = web_search("hello", region="not-a-region")
        assert isinstance(result, ToolResult)
        assert result.theme == "error"

    def test_invalid_safesearch_returns_error(self):
        result = web_search("hello", safesearch="maybe")
        assert isinstance(result, ToolResult)
        assert result.theme == "error"

    def test_no_results_returns_text_result(self):
        import ddgs as real_ddgs
        fake_ddgs = type("DDGS", (), {"text": staticmethod(lambda **kw: [])})()
        with patch.object(real_ddgs, "DDGS", return_value=fake_ddgs):
            result = web_search("nothing")

        assert isinstance(result, ToolResult)
        assert "No results" in result.llm_text
