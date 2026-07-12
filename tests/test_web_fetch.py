"""Tests for harness_core.tools.web_fetch — network mocked out."""

import json
from unittest.mock import patch, MagicMock

import pytest

from harness_core.tools.tool_result import ToolResult
from harness_core.tools.web_fetch import web_fetch


class _FakeResponse:
    def __init__(self, body=b"<html>hello</html>", content_type="text/html", url="https://example.com"):
        self._body = body
        self.headers = {"Content-Type": content_type}
        self.url = url
        self.status = 200

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestWebFetch:
    """web_fetch returns a ToolResult and hits urlopen with the expected URL."""

    def test_valid_url_returns_tool_result(self):
        fake_resp = _FakeResponse(body=b"page body", content_type="text/html; charset=utf-8")
        with patch("harness_core.tools.web_fetch.urlopen", return_value=fake_resp) as mock_urlopen:
            result = web_fetch("https://example.com/page")

        assert isinstance(result, ToolResult)
        assert result.type_tag == "json"
        data = json.loads(result.llm_text)
        assert data["status_code"] == 200
        assert data["text"] == "page body"
        # The network client was called with a Request built from the URL.
        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://example.com/page"

    def test_invalid_scheme_returns_error(self):
        result = web_fetch("ftp://example.com")
        assert isinstance(result, ToolResult)
        assert result.theme == "error"

    def test_empty_url_returns_error(self):
        result = web_fetch("")
        assert isinstance(result, ToolResult)
        assert result.theme == "error"

    def test_http_error_returns_error(self):
        import urllib.error

        err = urllib.error.HTTPError("https://x.com", 404, "Not Found", None, None)
        with patch("harness_core.tools.web_fetch.urlopen", side_effect=err):
            result = web_fetch("https://x.com/missing")

        assert isinstance(result, ToolResult)
        assert result.theme == "error"
